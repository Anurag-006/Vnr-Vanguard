import re

def get_sequence_strings(start_idx, end_idx):
    """
    Generates alphanumeric sequences skipping restricted characters.
    JNTUH/VNR follows a specific encoding after 99:
    1-99 -> 01, 02... 99
    100+ -> A0, A1... B0, B1... (skipping I, L, O, S)
    """
    valid_chars = "ABCDEFGHJKMNPQRTUVWXYZ"
    seq = []
    for i in range(start_idx, end_idx + 1):
        if i <= 99:
            # Standard two-digit padding for 01-99
            seq.append(f"{i:02d}")
        else:
            # Alphanumeric encoding for 100+
            offset = i - 100
            char_index = offset // 10
            digit = offset % 10
            
            # Prevent index out of bounds if a section is unusually large
            if char_index < len(valid_chars):
                char = valid_chars[char_index]
                seq.append(f"{char}{digit}")
    return seq

def generate_roll_numbers(year_prefix, section_key, section_info):
    """
    Constructs a full list of roll numbers for a specific section.
    Corrected: No extra '2' prepended. Format is YY071A....
    """
    section = section_info.get(section_key)
    if not section:
        return []
        
    rolls = []
    branch_code = section["code"]
    
    # Ensure year_prefix is a string (e.g., "23")
    year_str = str(year_prefix)
    
    # --- 1. Regular Students ---
    # Result: "23" + "071A" + "32" + "01" = "23071A3201"
    reg_seq = get_sequence_strings(section["reg_start"], section["reg_end"])
    for seq in reg_seq:
        rolls.append(f"{year_str}071A{branch_code}{seq}")
    
    # --- 2. Lateral Entry Students ---
    # Result: "24" + "075A" + "32" + "01" = "24075A3201"
    try:
        lat_year = str(int(year_str) + 1)
        lat_seq = get_sequence_strings(section["lat_start"], section["lat_end"])
        for seq in lat_seq:
            rolls.append(f"{lat_year}075A{branch_code}{seq}")
    except (ValueError, TypeError):
        pass
        
    return rolls

def safe_sgpa(student):
    """
    Sorting helper for the leaderboard.
    Ensures 'Withheld' or 'N/A' strings are treated as -1.0 so they 
    sink to the bottom of the rankings instead of causing a TypeError.
    """
    sgpa_value = student.get('sgpa', '0.00')
    
    # If SGPA is already a float/int
    if isinstance(sgpa_value, (int, float)):
        return float(sgpa_value)
    
    # If it's a string, attempt conversion
    try:
        # Clean any whitespace or colons
        clean_val = str(sgpa_value).replace(":", "").strip()
        return float(clean_val)
    except (ValueError, TypeError):
        # Return -1.0 for "Withheld", "N/A", or empty strings
        return -1.0

def validate_roll(roll):
    """
    Utility to check if a roll number string follows the standard 10-char format.
    Useful for the 'Friends Leaderboard' input validation.
    """
    pattern = r'^[2][0-9][0-7][1-5][15]A[0-9A-Z]{2}[0-9A-Z]{2}$'
    return bool(re.match(pattern, str(roll).upper()))