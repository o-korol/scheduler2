import sqlite3
from datetime import datetime
from itertools import permutations
from process_corequisites import process_corequisites
from retrieve_section_info import retrieve_section_info

# Function to check for conflicts with user's unavailability
def has_conflicts(scheduled_sections, new_section, unavailability_blocks):
    section_start = datetime.strptime(new_section["STime"], '%I:%M %p').time() if new_section["STime"] != 'nan' else None
    section_end = datetime.strptime(new_section["ETime"], '%I:%M %p').time() if new_section["ETime"] != 'nan' else None
    section_days = new_section["Mtg_Days"].split(', ') if new_section["Mtg_Days"] != 'nan' else []
    section_start_date = datetime.strptime(new_section["SDate"], '%Y-%m-%d %H:%M:%S')
    section_end_date = datetime.strptime(new_section["EDate"], '%Y-%m-%d %H:%M:%S')

    if section_start and section_end:
        for day in section_days:
            if day in unavailability_blocks:
                for block in unavailability_blocks[day]:
                    block_start = datetime.strptime(block[0], '%I:%M %p').time()
                    block_end = datetime.strptime(block[1], '%I:%M %p').time()
                    if section_start < block_end and section_end > block_start:
                        return True

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

# Function to generate all possible valid schedule combinations
def generate_combinations(cursor, sections_info, unavailability_blocks):
    valid_combinations = []
    course_list = list(sections_info.keys())

    def is_valid_combination(combination):
        scheduled_courses = set()
        scheduled_coreqs = set()

        for section, coreqs in combination:
            course_name = section["Name"].split('-')[0]
            if course_name in scheduled_courses:
                return False
            scheduled_courses.add(course_name)

            for coreq in coreqs:
                coreq_course_name = coreq["Name"].split('-')[0]
                if coreq_course_name in scheduled_coreqs:
                    return False
                scheduled_coreqs.add(coreq_course_name)

        return len(scheduled_courses) == len(course_list)

    for course_perm in permutations(course_list):
        for combination in permutations([(section, sections_info[course]) for course in course_perm for section in sections_info[course]], len(course_list)):
            if not any(has_conflicts([], section[0], unavailability_blocks) for section in combination):
                if is_valid_combination(combination):
                    valid_combinations.append(combination)
    return valid_combinations

# Function to print the summary of valid schedule combinations
def print_schedules(cursor, selected_courses, unavailable_courses, modality_preferences, valid_combinations):
    print("Generated valid schedule combinations:")
    for i, combination in enumerate(valid_combinations, start=1):
        print(f"Option {i}:")
        for section, coreqs in combination:
            if "Mtg_Days" in section:
                section_name = section["Name"]
                meeting_days = section["Mtg_Days"] if section["Mtg_Days"] != 'nan' else "Online"
                meeting_times = f"{section['STime']} - {section['ETime']}" if section['STime'] != 'nan' and section['ETime'] != 'nan' else ""
                print(f"  {section_name} ({meeting_days} {meeting_times})")
                if coreqs:
                    for coreq in coreqs:
                        if "Mtg_Days" in coreq:
                            coreq_name = coreq["Name"]
                            coreq_days = coreq["Mtg_Days"] if coreq["Mtg_Days"] != 'nan' else "Online"
                            coreq_times = f"{coreq['STime']} - {coreq['ETime']}" if coreq['STime'] != 'nan' and coreq['ETime'] != 'nan' else ""
                            print(f"    Corequisite: {coreq_name} ({coreq_days} {coreq_times})")
        print()

if __name__ == "__main__":
    # Connect to the SQLite database
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()

    # Example data
    selected_courses = ["BIO-172", "MAT-143"]
    unavailable_courses = ["AET-220"]
    modality_preferences = {"BIO-172": "LEC", "MAT-143": "HYB"}
    unavailability_blocks = {
        "Mon": [("12:00 AM", "09:00 AM"), ("03:00 PM", "11:59 PM")],
        "Tue": [("12:00 AM", "09:00 AM"), ("03:00 PM", "11:59 PM")],
        "Wed": [("12:00 AM", "09:00 AM"), ("03:00 PM", "11:59 PM")],
        "Thu": [("12:00 AM", "09:00 AM"), ("03:00 PM", "11:59 PM")],
        "Fri": [("12:00 AM", "09:00 AM"), ("03:00 PM", "11:59 PM")],
        "Sat": [("12:00 AM", "09:00 AM"), ("03:00 PM", "11:59 PM")]
    }

    # Retrieve sections info
    sections_info, section_columns = retrieve_section_info(cursor, selected_courses)
    sections_info, all_sections = process_corequisites(cursor, sections_info, section_columns)

    # Generate valid schedule combinations
    valid_combinations = generate_combinations(cursor, sections_info, unavailability_blocks)

    # Print the valid schedule combinations
    print_schedules(cursor, selected_courses, unavailable_courses, modality_preferences, valid_combinations)

    # Close the connection
    conn.close()
