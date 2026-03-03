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
    try:
        main_url = "https://vnrvjietexams.net/EduPrime3Exam/Results"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(main_url, headers=headers, timeout=10, verify=False)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            for script in soup.find_all('script'):
                if script.string and 'var data =' in script.string:
                    json_text = script.string.split('var data =')[1].strip().rstrip(';')
                    exam_list = json.loads(json_text)
                    return {
                        str(e.get('ExamId')): e.get('ExamName') 
                        for e in exam_list 
                        if "B.TECH" in e.get('ExamName', '').upper()
                    }
    except Exception as e:
        print(f"DEBUG ERROR: Dynamic exam fetch failed: {e}")
        
    return {"7463": "Default B.Tech Exam"}

def get_student_data(htno, exam_id):
    try:
        # User-Agent is critical to avoid datacenter blocks
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        res = requests.get(BASE_URL, params={'htno': htno, 'examId': exam_id}, headers=headers, timeout=10, verify=False)
        
        # LOGGING STATUS
        if res.status_code != 200:
            print(f"SCRAPER ERROR: Roll {htno} returned Status {res.status_code}")
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        page_text = soup.get_text().lower()

        name_tag = soup.find(string=lambda t: t and "Student Name" in t)
        if "withheld" in page_text or not name_tag:
            return {
                'roll': htno, 
                'name': "Result Withheld", 
                'sgpa': "Withheld", 
                'subjects': []
            }

        name = name_tag.parent.find_next('td').get_text(strip=True).replace(":", "")
        sgpa_tag = soup.find(string=lambda t: t and "SGPA" in t)
        sgpa = sgpa_tag.parent.find_next('td').get_text(strip=True).replace(":", "") if sgpa_tag else "0.00"
        
        if not sgpa or sgpa == "N/A":
            sgpa = "0.00"

        subjects = []
        table = soup.find('table')
        if table:
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
        print(f"SCRAPER CRITICAL: Failed for {htno} - {e}")
        return None

def fetch_batch(roll_numbers, exam_id):
    results = []
    print(f"SCRAPER: Starting batch fetch for {len(roll_numbers)} rolls.")
    fetch_func = partial(get_student_data, exam_id=exam_id)
    
    # max_workers=5 is safer for Render free tier to avoid RAM crashes
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for data in executor.map(fetch_func, roll_numbers):
            if data:
                results.append(data)
                
    print(f"SCRAPER: Batch fetch complete. Successfully parsed {len(results)}/{len(roll_numbers)} records.")
    return results