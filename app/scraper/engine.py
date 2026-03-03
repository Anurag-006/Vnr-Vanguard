import requests
import json
import concurrent.futures
import urllib3
import re
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
        
    return {"7463": "B.Tech Regular Exams"}


def get_student_data(htno, exam_id):
    """Scrapes results using the hidden AJAX endpoint."""
    
    # THE SECRET API ENDPOINT
    url = "https://vnrvjietexams.net/EduPrime3Exam/Results/Results"
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'X-Requested-With': 'XMLHttpRequest', # Important: Tells the server we are making an AJAX call
            'Referer': 'https://vnrvjietexams.net/EduPrime3Exam/Results'
        }
        
        # This endpoint uses GET based on the JS snippet we found
        res = requests.get(url, params={'htno': htno, 'examId': exam_id}, headers=headers, timeout=15, verify=False)
        
        if res.status_code != 200:
            return None
            
        # The server likely returns an HTML fragment (just the table), not a full page.
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # We look for the exact "Result Withheld" or "Invalid" message first
        page_text = soup.get_text().lower()
        if "invalid" in page_text or "not found" in page_text:
            return None # Skip invalid lateral entries
            
        name = "Result Withheld"
        sgpa = "0.00"
        
        all_elements = soup.find_all(['td', 'th', 'span', 'b', 'strong', 'div'])
        
        for i, el in enumerate(all_elements):
            text = el.get_text(strip=True).upper().replace(":", "").strip()
            
            if text == "STUDENT NAME" or text == "NAME OF THE STUDENT":
                if i + 1 < len(all_elements):
                    extracted_name = all_elements[i+1].get_text(strip=True).replace(":", "").strip()
                    if extracted_name: 
                        name = extracted_name
                        
            if text == "SGPA":
                if i + 1 < len(all_elements):
                    extracted_sgpa = all_elements[i+1].get_text(strip=True).replace(":", "").strip()
                    if extracted_sgpa and extracted_sgpa != "N/A":
                        sgpa = extracted_sgpa

        subjects = []
        tables = soup.find_all('table')
        if tables:
            results_table = max(tables, key=lambda t: len(t.find_all('tr')))
            
            for row in results_table.find_all('tr'):
                cols = row.find_all('td')
                if len(cols) >= 6:
                    first_col_text = cols[0].get_text(strip=True).upper()
                    if "S.NO" in first_col_text or "SUBJECT" in first_col_text:
                        continue
                        
                    grade_letter = cols[4].get_text(strip=True).upper()
                    subjects.append({
                        'code': cols[1].get_text(strip=True),
                        'title': cols[2].get_text(strip=True),
                        'grade': grade_letter,
                        'points': GRADE_POINTS.get(grade_letter, 0),
                        'result': cols[-1].get_text(strip=True).upper()
                    })
        
        # If we couldn't find a table or a name, the result is likely withheld
        if not subjects and name == "Result Withheld":
             return {
                'roll': htno, 
                'name': name, 
                'sgpa': "Withheld", 
                'subjects': []
            }
                    
        return {
            'roll': htno, 
            'name': name, 
            'sgpa': sgpa, 
            'subjects': subjects
        }
    except Exception as e:
        print(f"SCRAPER ERROR for {htno}: {e}")
        return None


def fetch_batch(roll_numbers, exam_id):
    results = []
    fetch_func = partial(get_student_data, exam_id=exam_id)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for data in executor.map(fetch_func, roll_numbers):
            if data:
                results.append(data)
    return results