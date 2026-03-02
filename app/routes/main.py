from flask import Blueprint, render_template, request, Response, abort, current_app
from flask_caching import Cache
import io, csv, os, re, datetime, hashlib
from scraper.engine import fetch_active_exams, fetch_batch, get_student_data
from scraper.utils import generate_roll_numbers, safe_sgpa
from scraper.constants import SECTION_INFO
from collections import Counter

main_bp = Blueprint('main', __name__)
cache = Cache() # Initialized via factory in app.py
STATS = {"hits": 0, "scrapes": 0}

def get_cache_timestamp(key):
    try:
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        # Ensure we look in the absolute path defined in app.config
        cache_path = os.path.join(current_app.config['CACHE_DIR'], key_hash)
        if os.path.exists(cache_path):
            ts = os.path.getmtime(cache_path)
            return datetime.datetime.fromtimestamp(ts).strftime('%I:%M %p, %d %b')
    except Exception as e:
        current_app.logger.error(f"Timestamp Error: {e}")
    return None

@main_bp.route('/')
def index():
    section = request.args.get('section')
    year = request.args.get('year')
    exams = fetch_active_exams()
    default_exam = list(exams.keys())[0] if exams else "7463"
    selected_exam = request.args.get('exam', default_exam)

    if not section or not year:
        return render_template('dashboard.html', students=None, sections=SECTION_INFO.keys(),
                               available_exams=exams, selected_exam=selected_exam)

    cache_key = f"{section}_{year}_{selected_exam}"
    data = cache.get(cache_key)
    last_updated = get_cache_timestamp(cache_key)

    if data:
        STATS["hits"] += 1
    else:
        # Protect the portal with a strict scrape-only limit
        @current_app.limiter.limit("5 per minute")
        def scrape_logic():
            STATS["scrapes"] += 1
            rolls = generate_roll_numbers(year, section, SECTION_INFO)
            batch_data = fetch_batch(rolls, selected_exam)
            batch_data.sort(key=safe_sgpa, reverse=True)
            cache.set(cache_key, batch_data, timeout=86400)
            return batch_data
        
        try:
            data = scrape_logic()
            last_updated = "Just now"
        except Exception:
            abort(429)

    return render_template('dashboard.html', students=data, sections=SECTION_INFO.keys(), 
                           selected_section=section, selected_year=year,
                           available_exams=exams, selected_exam=selected_exam,
                           last_updated=last_updated)

@main_bp.route('/report/<roll_no>')
def report_card(roll_no):
    exams = fetch_active_exams()
    selected_exam = request.args.get('exam', list(exams.keys())[0])
    student = get_student_data(roll_no, selected_exam)
    if not student:
        abort(404)
    return render_template('report_card.html', student=student)

@main_bp.route('/friends', methods=['GET', 'POST'])
def friends_leaderboard():
    rolls_input = request.form.get('roll_numbers', '')
    class_results = []
    exams = fetch_active_exams()
    selected_exam = request.form.get('exam') or request.args.get('exam') or list(exams.keys())[0]
    
    if rolls_input:
        raw_rolls = re.findall(r'[a-zA-Z0-9]{10}', rolls_input)
        valid_rolls = list(set([r.upper() for r in raw_rolls]))
        if valid_rolls:
            class_results = fetch_batch(valid_rolls, selected_exam)
            class_results.sort(key=safe_sgpa, reverse=True)

    return render_template('friends.html', students=class_results, saved_input=rolls_input,
                           available_exams=exams, selected_exam=selected_exam)

@main_bp.route('/export')
def export_csv():
    section = request.args.get('section', 'CSBS')
    year = request.args.get('year', os.getenv("YEAR_PREFIX", "23"))
    exams = fetch_active_exams()
    selected_exam = request.args.get('exam', list(exams.keys())[0])
    
    cache_key = f"{section}_{year}_{selected_exam}"
    all_student_data = cache.get(cache_key)
    
    if not all_student_data:
        rolls = generate_roll_numbers(year, section, SECTION_INFO)
        all_student_data = fetch_batch(rolls, selected_exam)
        all_student_data.sort(key=safe_sgpa, reverse=True)

    all_subject_titles = set()
    for student in all_student_data:
        for sub in student.get('subjects', []):
            all_subject_titles.add(sub['title'])
    
    sorted_subjects = sorted(list(all_subject_titles))
    output = io.StringIO()
    writer = csv.writer(output)
    header = ['Roll Number', 'Name'] + sorted_subjects + ['SGPA', 'Final Verdict']
    writer.writerow(header)
    
    for student in all_student_data:
        grade_map = {sub['title']: sub['grade'] for sub in student.get('subjects', [])}
        row = [student['roll'], student['name']]
        for subject in sorted_subjects:
            row.append(grade_map.get(subject, "N/A"))
            
        if student['name'] == "Result Withheld":
            verdict = "WITHHELD"
        else:
            failed = any(sub['result'] == 'FAIL' for sub in student.get('subjects', []))
            verdict = "FAIL" if failed else "PASS"
            
        row.extend([student['sgpa'], verdict])
        writer.writerow(row)
    
    return Response(output.getvalue(), mimetype="text/csv",
                    headers={"Content-disposition": f"attachment; filename={section}_Results_{year}.csv"})

@main_bp.route('/status')
def status():
    cache_count = 0
    if os.path.exists('flask_cache'):
        cache_count = len([f for f in os.listdir('flask_cache') if os.path.isfile(os.path.join('flask_cache', f))])
    return render_template('status.html', stats=STATS, cache_files=cache_count, secret_key=os.getenv("MY_SECRET_KEY"))

@main_bp.route('/refresh')
def refresh():
    if request.args.get('key') != os.getenv("MY_SECRET_KEY"):
        abort(403)
    cache.clear()
    return "Cache cleared successfully!"

@main_bp.route('/stats')
def class_stats():
    section = request.args.get('section')
    year = request.args.get('year')
    exam = request.args.get('exam')
    cache_key = f"{section}_{year}_{exam}"
    students = cache.get(cache_key)
    
    if not students:
        return "No data found for these stats.", 404

    total_students = len(students)
    passed_students = 0
    total_sgpa = 0.0
    grade_counts = Counter()
    subject_data = {} 
    
    for s in students:
        try:
            val = float(s['sgpa'])
            total_sgpa += val
        except: pass

        failed = any(sub['result'] == 'FAIL' for sub in s['subjects'])
        if not failed and s['name'] != "Result Withheld":
            passed_students += 1

        for sub in s['subjects']:
            grade_counts[sub['grade']] += 1
            name = sub['title']
            if name not in subject_data:
                subject_data[name] = {'pass': 0, 'fail': 0}
            if sub['result'] == 'PASS':
                subject_data[name]['pass'] += 1
            else:
                subject_data[name]['fail'] += 1

    grade_order = {"O": 0, "A+": 1, "A": 2, "B+": 3, "B": 4, "C": 5, "F": 6, "AB": 7}
    sorted_grades = dict(sorted(grade_counts.items(), key=lambda x: grade_order.get(x[0], 99)))

    stats = {
        'avg_sgpa': round(total_sgpa / total_students, 2) if total_students > 0 else 0,
        'pass_percentage': round((passed_students / total_students) * 100, 1) if total_students > 0 else 0,
        'total': total_students,
        'passed': passed_students,
        'failed': total_students - passed_students,
        'grades': sorted_grades,
        'subjects': subject_data
    }
    return render_template('stats.html', stats=stats, section=section)