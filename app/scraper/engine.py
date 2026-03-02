import requests
import json
import concurrent.futures
import urllib3
from bs4 import BeautifulSoup
from functools import partial
from flask import current_app as app
from .constants import BASE_URL, GRADE_POINTS

# Suppress SSL warnings for the college portal
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_active_exams():
    """
    Extracts Exam IDs directly from the hidden JSON script on the college site.
    This prevents the app from breaking when new semesters are added.
    """
    try:
        main_url = "https://vnrvjietexams.net/EduPrime3Exam/Results"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        res = requests.get(main_url, headers=headers, timeout=10, verify=False)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for script in soup.find_all('script'):
                if script.string and 'var data =' in script.string:
                    # Isolate the JSON string from the JavaScript variable assignment
                    json_text = script.string.split('var data =')[1].strip().rstrip(';')
                    
                    exam_list = json.loads(json_text)
                    # Filter for B.Tech exams and return a dict {ExamId: ExamName}
                    return {
                        str(e.get('ExamId')): e.get('ExamName') 
                        for e in exam_list 
                        if "B.TECH" in e.get('ExamName', '').upper()
                    }
    except Exception as e:
        app.logger.error(f"Dynamic exam fetch failed: {e}")
        
    # Fallback to a known Exam ID if the dynamic fetch fails
    return {"7463": "Default B.Tech Exam"}

def get_student_data(htno, exam_id):
    """
    Scrapes results for a single roll number.
    Handles withheld status and table parsing.
    """
    try:
        res = requests.get(BASE_URL, params={'htno': htno, 'examId': exam_id}, timeout=7, verify=False)
        if res.status_code != 200:
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        page_text = soup.get_text().lower()

        # Handle specific "Withheld" text or missing data
        name_tag = soup.find(string=lambda t: t and "Student Name" in t)
        if "withheld" in page_text or not name_tag:
            return {
                'roll': htno, 
                'name': "Result Withheld", 
                'sgpa': "Withheld", 
                'subjects': []
            }

        name = name_tag.parent.find_next('td').get_text(strip=True).replace(":", "")
        
        # Handle SGPA extraction
        sgpa_tag = soup.find(string=lambda t: t and "SGPA" in t)
        sgpa = sgpa_tag.parent.find_next('td').get_text(strip=True).replace(":", "") if sgpa_tag else "0.00"
        
        # Ensure we have a numeric-like value for sorting later
        if not sgpa or sgpa == "N/A":
            sgpa = "0.00"

        subjects = []
        table = soup.find('table')
        if table:
            # Skip header row
            for row in table.find_all('tr')[1:]:
                cols = row.find_all('td')
                if len(cols) >= 6:
                    grade_letter = cols[4].text.strip().upper()
                    subjects.append({
                        'code': cols[1].text.strip(),
                        'title': cols[2].text.strip(),
                        'grade': grade_letter,
                        'points': GRADE_POINTS.get(grade_letter, "-"),
                        'result': cols[-1].text.strip()
                    })
                    
        return {
            'roll': htno, 
            'name': name, 
            'sgpa': sgpa, 
            'subjects': subjects
        }
    except Exception as e:
        # Silently fail for individual students to keep the batch moving
        return None

def fetch_batch(roll_numbers, exam_id):
    """
    Uses a ThreadPool to fetch data for multiple students in parallel.
    Optimized for 10 workers to balance speed vs. server safety.
    """
    results = []
    # Partial allows us to pass the exam_id fixed to the get_student_data function
    fetch_func = partial(get_student_data, exam_id=exam_id)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # map() maintains the order of roll numbers
        for data in executor.map(fetch_func, roll_numbers):
            if data:
                results.append(data)
                
    return results