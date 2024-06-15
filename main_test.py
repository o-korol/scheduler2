import sqlite3
from datetime import datetime
from itertools import permutations
import time

def retrieve_section_info(cursor, selected_courses):
    start_time = time.time()
    sections_info = {}
    section_columns = []
    for course in selected_courses:
        cursor.execute("""
            SELECT Name, Avail_Seats, Printed_Comments, Corequisite, STime, ETime, SDate, EDate, Mtg_Days, Method, Credits, Restricted_Section, Cohort
            FROM schedule
            WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
        """, (course,))
        sections = cursor.fetchall()
        # if column is not defined yet, retrieve column name from cursor.description attribute,
        # which provides metadata about the columns; the name if the first item in the metadata
        if not section_columns:
            section_columns = [desc[0] for desc in cursor.description]
        sections_info[course] = [dict(zip(section_columns, section)) for section in sections]
    end_time = time.time()
    retrieval_time = end_time - start_time
    print(f"Time to retrieve section info: {retrieval_time:.2f} seconds")
    return sections_info, section_columns, retrieval_time

def process_corequisites(cursor, sections_info, section_columns):
    start_time = time.time()
    all_sections = {}
    processed_sections = set()
    updated_sections_info = {}

    for course, sections in sections_info.items():
        updated_sections_info[course] = []
        for section in sections:
            section_name = section["Name"]
            coreqs = section["Corequisite"]
            if section_name not in processed_sections:
                processed_sections.add(section_name)
                if coreqs:
                    coreq_list = coreqs.split(',')
                    specific_coreqs = []
                    for coreq in coreq_list:
                        coreq = coreq.strip()
                        cursor.execute("""
                            SELECT Name, Avail_Seats, Printed_Comments, Corequisite, STime, ETime, SDate, EDate, Mtg_Days, Method, Restricted_Section, Cohort
                            FROM schedule
                            WHERE Name = ? AND Status = 'A' AND Avail_Seats > 0
                        """, (coreq,))
                        coreq_section = cursor.fetchone()
                        if coreq_section:
                            coreq_section = dict(zip(section_columns, coreq_section))
                            specific_coreqs.append(coreq_section)
                            processed_sections.add(coreq_section["Name"])
                    updated_sections_info[course].append((section, specific_coreqs))
                else:
                    updated_sections_info[course].append((section, []))
            all_sections[section_name] = section

    end_time = time.time()
    corequisite_time = end_time - start_time
    print(f"Time to process corequisites: {corequisite_time:.2f} seconds")
    return updated_sections_info, all_sections, corequisite_time

def generate_combinations(sections_info):
    start_time = time.time()
    valid_combinations = []
    course_list = list(sections_info.keys())

    def is_valid_combination(combination):
        scheduled_courses = set()
        for section, coreqs in combination:
            course_name = '-'.join(section["Name"].split('-')[:2])
            if course_name in scheduled_courses:
                return False
            scheduled_courses.add(course_name)
        return len(scheduled_courses) == len(course_list)

    for course_perm in permutations(course_list):
        for combination in permutations([section for course in course_perm for section in sections_info[course] if isinstance(section, tuple)], len(course_list)):
            if is_valid_combination(combination):
                valid_combinations.append(combination)

    end_time = time.time()
    combination_time = end_time - start_time
    print(f"Time to generate combinations: {combination_time:.2f} seconds")
    return valid_combinations, combination_time

def validate_combinations_with_coreqs(combinations_without_coreqs, sections_info, unavailability_blocks):
    start_time = time.time()
    valid_combinations = []

    for combination in combinations_without_coreqs:
        base_combination = [section[0] for section in combination]
        additional_combinations = [[]]

        for section, coreqs in combination:
            if coreqs:
                new_combinations = []
                for coreq in coreqs:
                    for combo in additional_combinations:
                        new_combo = combo + [coreq]
                        new_combinations.append(new_combo)
                additional_combinations = new_combinations

        for extra_combination in additional_combinations:
            full_combination = base_combination + extra_combination
            if is_valid_combination(full_combination, unavailability_blocks):
                valid_combinations.append(full_combination)

    end_time = time.time()
    validation_time = end_time - start_time
    print(f"Time to validate combinations with coreqs: {validation_time:.2f} seconds")
    return valid_combinations, validation_time

'''
def is_valid_combination(combination, unavailability_blocks):
    """
    Check if a combination of sections is valid by ensuring there are no intrinsic or extrinsic conflicts.
    """
    scheduled_sections = []

    for section in combination:
        if has_intrinsic_conflict(scheduled_sections, section) or has_extrinsic_conflict(section, unavailability_blocks):
            return False
        scheduled_sections.append(section)

    return True
'''

'''Being tested:  applies intrinsic and extrinsic filters sequentially '''
def is_valid_combination(combination, unavailability_blocks):
    """
    Check if a combination of sections is valid by ensuring there are no intrinsic or extrinsic conflicts.
    """
    scheduled_sections = []

    for section in combination:
        # Check intrinsic conflicts first
        if has_intrinsic_conflict(scheduled_sections, section):
            return False
        # Check extrinsic conflicts only if intrinsic check passes
        if has_extrinsic_conflict(section, unavailability_blocks):
            return False
        scheduled_sections.append(section)

    return True

def has_intrinsic_conflict(scheduled_sections, new_section):
    """
    Check for conflicts between scheduled sections (intrinsic conflicts).
    """
    section_start = datetime.strptime(new_section["STime"], '%I:%M %p').time() if new_section["STime"] != 'nan' else None
    section_end = datetime.strptime(new_section["ETime"], '%I:%M %p').time() if new_section["ETime"] != 'nan' else None
    section_days = new_section["Mtg_Days"].split(', ') if new_section["Mtg_Days"] != 'nan' else []
    section_start_date = datetime.strptime(new_section["SDate"], '%Y-%m-%d %H:%M:%S')
    section_end_date = datetime.strptime(new_section["EDate"], '%Y-%m-%d %H:%M:%S')

    if section_start and section_end:
        for scheduled_section in scheduled_sections:
            scheduled_start = datetime.strptime(scheduled_section["STime"], '%I:%M %p').time() if scheduled_section["STime"] != 'nan' else None
            scheduled_end = datetime.strptime(scheduled_section["ETime"], '%I:%M %p').time() if scheduled_section["ETime"] != 'nan' else None
            scheduled_days = scheduled_section["Mtg_Days"].split(', ') if scheduled_section["Mtg_Days"] != 'nan' else []
            scheduled_start_date = datetime.strptime(scheduled_section["SDate"], '%Y-%m-%d %H:%M:%S')
            scheduled_end_date = datetime.strptime(scheduled_section["EDate"], '%Y-%m-%d %H:%M:%S')

            if (section_start_date <= scheduled_end_date and section_end_date >= scheduled_start_date):
                if section_start and section_end and scheduled_start and scheduled_end:
                    for day in section_days:
                        if day in scheduled_days:
                            if section_start < scheduled_end and section_end > scheduled_start:
                                return True
    return False

def has_extrinsic_conflict(new_section, unavailability_blocks):
    """
    Check for conflicts between a section and unavailability blocks (extrinsic conflicts).
    """
    section_start = datetime.strptime(new_section["STime"], '%I:%M %p').time() if new_section["STime"] != 'nan' else None
    section_end = datetime.strptime(new_section["ETime"], '%I:%M %p').time() if new_section["ETime"] != 'nan' else None
    section_days = new_section["Mtg_Days"].split(', ') if new_section["Mtg_Days"] != 'nan' else []

    day_map = {'M': 'Mon', 'T': 'Tue', 'W': 'Wed', 'TH': 'Thu', 'F': 'Fri', 'S': 'Sat'}

    for day in section_days:
        mapped_day = day_map.get(day)
        if not mapped_day:
            continue

        if mapped_day in unavailability_blocks:
            for block in unavailability_blocks[mapped_day]:
                block_start = datetime.strptime(block[0], '%I:%M %p').time()
                block_end = datetime.strptime(block[1], '%I:%M %p').time()

                if section_start < block_end and section_end > block_start:
                    return True

    return False

def score_gaps(combination, config):
    """
    Calculate the gap score for a given combination.
    """
    gap_score = 0
    mandatory_break_start = datetime.strptime(config["gap_weights"]["mandatory_break_start"], '%I:%M %p').time()
    mandatory_break_end = datetime.strptime(config["gap_weights"]["mandatory_break_end"], '%I:%M %p').time()
    max_allowed_gap = config["gap_weights"]["max_allowed_gap"]

    day_map = {'M': 'Mon', 'T': 'Tue', 'W': 'Wed', 'TH': 'Thu', 'F': 'Fri', 'S': 'Sat'}

    for day in day_map.keys():
        day_sections = [s for s in combination if day in s["Mtg_Days"]]
        day_sections.sort(key=lambda s: datetime.strptime(s["STime"], '%I:%M %p').time() if s["STime"] != 'nan' else datetime.strptime('12:00 AM', '%I:%M %p').time())

        for i in range(1, len(day_sections)):
            prev_section = day_sections[i - 1]
            curr_section = day_sections[i]

            prev_end = datetime.strptime(prev_section["ETime"], '%I:%M %p').time() if prev_section["ETime"] != 'nan' else None
            curr_start = datetime.strptime(curr_section["STime"], '%I:%M %p').time() if curr_section["STime"] != 'nan' else None

            if prev_end and curr_start:
                if day in ['M', 'W', 'F'] and prev_end <= mandatory_break_start and curr_start >= mandatory_break_end:
                    continue  # Skip mandatory break gaps
                gap_minutes = (datetime.combine(datetime.min, curr_start) - datetime.combine(datetime.min, prev_end)).seconds / 60
                if gap_minutes > max_allowed_gap:
                    gap_hours = round(gap_minutes / 60)
                    gap_score += (gap_hours ** 2)

    return gap_score

def calculate_modality_score(combination, modality_preferences):
    """
    Calculate the score based on the modality preferences of the student.
    """
    modality_score = 0

    for section in combination:
        course_name = '-'.join(section["Name"].split('-')[:2])
        section_modality = section["Method"]
        preferred_modality = modality_preferences.get(course_name)

        if preferred_modality and section_modality != preferred_modality:
            modality_score += 1

    return modality_score

def calculate_days_on_campus(combination, day_weights):
    """
    Calculate the score based on the number of days on campus.
    """
    days_on_campus = set()
    for section in combination:
        if section["Method"] != "ONLIN":
            days_on_campus.update(section["Mtg_Days"].split(', ') if section["Mtg_Days"] != 'nan' else [])

    num_days = len(days_on_campus)
    return day_weights.get(num_days, max(day_weights.values()))  # Return the weight for the number of days or the max weight if not defined

def combined_score(combination, config):
    modality_score = calculate_modality_score(combination, config["preferences"])
    days_score = calculate_days_on_campus(combination, config["day_weights"])
    gap_score = score_gaps(combination, config)
    combined_score = (
        config["weights"]["modality"] * modality_score +
        config["weights"]["days"] * days_score +
        config["weights"]["gaps"] * gap_score
    )
    return combined_score, modality_score, days_score, gap_score

def sort_combination(combination):
    """
    Sort the sections within a combination by the start time of their first meeting day.
    """
    # Define a mapping from days of the week to numbers
    day_to_number = {'M': 0, 'T': 1, 'W': 2, 'TH': 3, 'F': 4, 'S': 5}

    def sort_key(section):
        # Check if the section is online
        if section["Method"] == "ONLIN":
            return (7, None)  # Online sections get assigned to 8th day of the week, so that they are printed last
        # Extract the first meeting day and start time
        first_day = section["Mtg_Days"].split(', ')[0] if section["Mtg_Days"] != 'nan' else 'nan'
        day_number = day_to_number.get(first_day, 6)  # Use 6 for 'nan' to sort them after regular days
        start_time = datetime.strptime(section["STime"], '%I:%M %p').time() if section["STime"] != 'nan' else datetime.strptime('12:00 AM', '%I:%M %p').time()
        return (day_number, start_time)

    # Sort the sections within each combination
    return sorted(combination, key=sort_key)

def print_summary(valid_combinations_with_scores):
    """
    Print the valid schedule combinations sorted by combined score.
    """
    # Sort combinations by combined score first
    valid_combinations_with_scores.sort(key=lambda x: x[1])

    print("Generated valid schedule combinations:")
    for i, (combination, combined_score, modality_score, days_score, gap_score) in enumerate(valid_combinations_with_scores, start=1):
        sorted_combination = sort_combination(combination)
        print(f"Option {i} (combined score = {combined_score}, modality score = {modality_score}, days score = {days_score}, gap score = {gap_score}):")
        for section in sorted_combination:
            section_name = section["Name"]
            meeting_days = section["Mtg_Days"] if section["Mtg_Days"] != 'nan' else "Online"
            meeting_times = f"{section['STime']} - {section['ETime']}" if section['STime'] != 'nan' and section['ETime'] != 'nan' else ""
            print(f"  {section_name} ({meeting_days} {meeting_times})")
        print()

    # Re-print top 50 combinations
    if len(valid_combinations_with_scores) > 50:
        print("Top 50 schedule combinations:")
        for i, (combination, combined_score, modality_score, days_score, gap_score) in enumerate(valid_combinations_with_scores[:50], start=1):
            sorted_combination = sort_combination(combination)
            print(f"Option {i} (combined score = {combined_score}, modality score = {modality_score}, days score = {days_score}, gap score = {gap_score}):")
            for section in sorted_combination:
                section_name = section["Name"]
                meeting_days = section["Mtg_Days"] if section["Mtg_Days"] != 'nan' else "Online"
                meeting_times = f"{section['STime']} - {section['ETime']}" if section['STime'] != 'nan' and section['ETime'] != 'nan' else ""
                print(f"  {section_name} ({meeting_days} {meeting_times})")
            print()

def main():
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()

    from user_input import get_course_names
    selected_courses, unavailable_courses, modality_preferences = get_course_names(cursor, 8)

    from availability import get_availability
    availability, unavailability_blocks = get_availability()

    start_script_time = time.time()

    sections_info, section_columns, retrieval_time = retrieve_section_info(cursor, selected_courses)
    sections_info, all_sections, corequisite_time = process_corequisites(cursor, sections_info, section_columns)

    combinations_without_coreqs, combination_time = generate_combinations(sections_info)
    valid_combinations, validation_time = validate_combinations_with_coreqs(combinations_without_coreqs, sections_info, unavailability_blocks)

    config = {
        "weights": { "modality": 3, "days": 1, "gaps": 1 },
        "preferences": modality_preferences,
        "day_weights": {1: 0, 2: 1, 3: 2, 4: 3, 5: 4},
        "gap_weights": {
            "mandatory_break_start": "12:15 PM",
            "mandatory_break_end": "1:15 PM",
            "max_allowed_gap": 20
        }
    }

    start_scoring_time = time.time()
    valid_combinations_with_scores = []
    for combination in valid_combinations:
        score = combined_score(combination, config)
        valid_combinations_with_scores.append((combination, *score))
    end_scoring_time = time.time()
    scoring_time = end_scoring_time - start_scoring_time
    print(f"Total time to score all combinations: {scoring_time:.2f} seconds")

    print_summary(valid_combinations_with_scores)

    conn.close()

    end_script_time = time.time()
    total_script_time = end_script_time - start_script_time
    print(f"Total script execution time (excluding user input): {total_script_time:.2f} seconds")

    # Print summary of all timings
    print("\n--- Performance Summary ---")
    print(f"Time to retrieve section info: {retrieval_time:.2f} seconds")
    print(f"Time to process corequisites: {corequisite_time:.2f} seconds")
    print(f"Time to generate combinations: {combination_time:.2f} seconds")
    print(f"Time to validate combinations with coreqs: {validation_time:.2f} seconds")
    print(f"Total time to score all combinations: {scoring_time:.2f} seconds")
    print(f"Total script execution time (excluding user input): {total_script_time:.2f} seconds")

if __name__ == "__main__":
    main()
