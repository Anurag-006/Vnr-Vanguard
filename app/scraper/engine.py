import requests
import json
import concurrent.futures
import urllib3
import re
from bs4 import BeautifulSoup
from functools import partial
from flask import current_app as app
from .constants import GRADE_POINTS

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# THE CORRECT PORTAL URL
RESULTS_URL = "https://vnrvjietexams.net/EduPrime3Exam/Results"

def get_student_data(htno, exam_id):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': RESULTS_URL
        }
        
        # We use HTNO and examId as params because the portal expects them to load the record
        res = requests.get(RESULTS_URL, params={'htno': htno, 'examId': exam_id}, headers=headers, timeout=15, verify=False)
        
        if res.status_code != 200:
            print(f"SCRAPER ERROR: Roll {htno} returned Status {res.status_code}")
            return None
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 1. Identify the Name Label (using regex for flexibility)
        name_label = soup.find(string=re.compile(r'Student Name', re.IGNORECASE))
        
        # If we can't find the Name label, it's either an invalid roll or withheld
        if not name_label:
            return {
                'roll': htno, 
                'name': "Result Withheld/Invalid", 
                'sgpa': "0.00", 
                'subjects': []
            }

        # Navigate to the value cell (VNR usually uses a <td> containing the label followed by a <td> with the value)
        try:
            name = name_label.find_parent('td').find_next_sibling('td').get_text(strip=True).replace(":", "")
        except:
            name = "Unknown Student"

        # 2. Extract SGPA
        sgpa = "0.00"
        sgpa_label = soup.find(string=re.compile(r'SGPA', re.IGNORECASE))
        if sgpa_label:
            try:
                sgpa_val = sgpa_label.find_parent('td').find_next_sibling('td').get_text(strip=True).replace(":", "")
                sgpa = sgpa_val if sgpa_val and sgpa_val != "N/A" else "0.00"
            except: pass

        # 3. Parse the Results Table
        subjects = []
        # Usually the results are in the only <table> with more than 3 rows
        tables = soup.find_all('table')
        if tables:
            # Find the main table (usually contains 'Subject Code' in the header)
            target_table = None
            for t in tables:
                if "Subject" in t.get_text():
                    target_table = t
                    break
            
            if target_table:
                for row in target_table.find_all('tr'):
                    cols = row.find_all('td')
                    # Expecting: S.No, Code, Title, Internals, Externals, Grade, Credits, Result
                    if len(cols) >= 6:
                        # Skip Header
                        if "Subject" in cols[1].get_text() or "S.No" in cols[0].get_text():
                            continue
                            
                        grade_letter = cols[4].get_text(strip=True).upper()
                        subjects.append({
                            'code': cols[1].get_text(strip=True),
                            'title': cols[2].get_text(strip=True),
                            'grade': grade_letter,
                            'points': GRADE_POINTS.get(grade_letter, 0),
                            'result': cols[-1].get_text(strip=True).upper()
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
    print(f"SCRAPER: Fetching {len(roll_numbers)} students via {RESULTS_URL}")
    
    fetch_func = partial(get_student_data, exam_id=exam_id)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        for data in executor.map(fetch_func, roll_numbers):
            if data:
                results.append(data)
                
    print(f"SCRAPER: Batch complete. Parsed {len(results)}/{len(roll_numbers)} records.")
    return results