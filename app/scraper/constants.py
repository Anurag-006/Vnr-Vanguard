import os

# Base URL for the scraping engine - no hardcoded default
BASE_URL = os.getenv("BASE_URL")

# Standard Grade to Point mapping for VNR/JNTUH 10-point scale
GRADE_POINTS = {
    'O': 10, 
    'A+': 9, 
    'A': 8, 
    'B+': 7, 
    'B': 6, 
    'C': 5, 
    'F': 0, 
    'AB': 0, 
    'ABSENT': 0
}

# Exhaustive section mapping based on VNR VJIET departmental distribution
SECTION_INFO = {
    "AE": {"code": "24", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "AIDS": {"code": "72", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "CE-1": {"code": "01", "reg_start": 1, "reg_end": 64, "lat_start": 1, "lat_end": 6},
    "CE-2": {"code": "01", "reg_start": 65, "reg_end": 128, "lat_start": 7, "lat_end": 12},
    "CSBS": {"code": "32", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 9},
    "CSE-1": {"code": "05", "reg_start": 1, "reg_end": 68, "lat_start": 1, "lat_end": 6},
    "CSE-2": {"code": "05", "reg_start": 69, "reg_end": 136, "lat_start": 7, "lat_end": 12},
    "CSE-3": {"code": "05", "reg_start": 137, "reg_end": 204, "lat_start": 13, "lat_end": 18},
    "CSE-4": {"code": "05", "reg_start": 205, "reg_end": 272, "lat_start": 19, "lat_end": 24},
    "CSE-AIML-1": {"code": "66", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "CSE-AIML-2": {"code": "66", "reg_start": 67, "reg_end": 132, "lat_start": 7, "lat_end": 12},
    "CSE-AIML-3": {"code": "66", "reg_start": 133, "reg_end": 198, "lat_start": 13, "lat_end": 18},
    "CSE-CYS": {"code": "62", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "CSE-DS-1": {"code": "67", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "CSE-DS-2": {"code": "67", "reg_start": 67, "reg_end": 132, "lat_start": 7, "lat_end": 12},
    "CSE-DS-3": {"code": "67", "reg_start": 133, "reg_end": 198, "lat_start": 13, "lat_end": 18},
    "CSE-IoT": {"code": "69", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "ECE-1": {"code": "04", "reg_start": 1, "reg_end": 64, "lat_start": 1, "lat_end": 6},
    "ECE-2": {"code": "04", "reg_start": 65, "reg_end": 128, "lat_start": 7, "lat_end": 12},
    "ECE-3": {"code": "04", "reg_start": 129, "reg_end": 192, "lat_start": 13, "lat_end": 18},
    "ECE-4": {"code": "04", "reg_start": 193, "reg_end": 256, "lat_start": 19, "lat_end": 24},
    "EEE-1": {"code": "02", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "EEE-2": {"code": "02", "reg_start": 67, "reg_end": 132, "lat_start": 7, "lat_end": 12},
    "EIE-1": {"code": "10", "reg_start": 1, "reg_end": 64, "lat_start": 1, "lat_end": 6},
    "EIE-2": {"code": "10", "reg_start": 65, "reg_end": 128, "lat_start": 7, "lat_end": 12},
    "IT-1": {"code": "12", "reg_start": 1, "reg_end": 66, "lat_start": 1, "lat_end": 6},
    "IT-2": {"code": "12", "reg_start": 67, "reg_end": 132, "lat_start": 7, "lat_end": 12},
    "IT-3": {"code": "12", "reg_start": 133, "reg_end": 200, "lat_start": 13, "lat_end": 18},
    "ME-1": {"code": "03", "reg_start": 1, "reg_end": 64, "lat_start": 1, "lat_end": 6},
    "ME-2": {"code": "03", "reg_start": 65, "reg_end": 128, "lat_start": 7, "lat_end": 12}
}