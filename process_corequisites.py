import sqlite3
from datetime import datetime
from itertools import permutations

def retrieve_section_info(cursor, selected_courses):
    sections_info = {}
    section_columns = []
    for course in selected_courses:
        cursor.execute("""
            SELECT Name, Avail_Seats, Printed_Comments, Corequisite, PTECH, STime, ETime, SDate, EDate, Mtg_Days, Method, Credits
            FROM schedule
            WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
        """, (course,))
        sections = cursor.fetchall()
        if not section_columns:
            section_columns = [desc[0] for desc in cursor.description]
        sections_info[course] = [dict(zip(section_columns, section)) for section in sections]
    return sections_info, section_columns

def process_corequisites(cursor, sections_info, section_columns):
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
                            SELECT Name, Avail_Seats, Printed_Comments, Corequisite, PTECH, STime, ETime, SDate, EDate, Mtg_Days, Method
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

    return updated_sections_info, all_sections

def generate_combinations(cursor, sections_info):
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
        for combination in permutations([section for course in course_perm for section in sections_info[course] if isinstance(section, tuple)], len(course_list)):
            if is_valid_combination(combination):
                valid_combinations.append(combination)
    return valid_combinations

def validate_combinations_with_coreqs(combinations_without_coreqs, corequisites_info, cursor):
    valid_combinations = []

    for combination in combinations_without_coreqs:
        current_schedule = []
        for section in combination:
            current_schedule.append(section[0])
            coreqs = section[1]
            for coreq_section in coreqs:
                if not has_conflicts(current_schedule, coreq_section):
                    current_schedule.append(coreq_section)
                else:
                    break
        if len(current_schedule) == len(combination) + sum(len(section[1]) for section in combination):
            valid_combinations.append(current_schedule)

    return valid_combinations

def has_conflicts(scheduled_sections, new_section):
    section_start = datetime.strptime(new_section["STime"], '%I:%M %p').time() if new_section["STime"] != 'nan' else None
    section_end = datetime.strptime(new_section["ETime"], '%I:%M %p').time() if new_section["ETime"] != 'nan' else None
    section_days = new_section["Mtg_Days"].split(', ') if new_section["Mtg_Days"] != 'nan' else []
    section_start_date = datetime.strptime(new_section["SDate"], '%Y-%m-%d %H:%M:%S')
    section_end_date = datetime.strptime(new_section["EDate"], '%Y-%m-%d %H:%M:%S')

    if section_start and section_end:
        for day in section_days:
            for block in unavailability_blocks.get(day, []):
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

def summarize_user_input(cursor, selected_courses, unavailable_courses, modality_preferences):
    total_credits = 0
    print("\nYou selected the following courses:")
    for course_name in selected_courses:
        cursor.execute("SELECT Short_Title, Credits, Corequisite FROM schedule WHERE Course_Name = ?", (course_name,))
        course_info = cursor.fetchone()
        if course_info:
            short_title, credits, coreqs = course_info
            total_credits += credits
            coreqs_text = f"(has corequisites: {coreqs})" if coreqs else ""
            credits_text = f"{int(credits)}" if credits.is_integer() else f"{credits:.1f}"
            print(f"{course_name} \"{short_title}\" {credits_text} credits {coreqs_text}")

    total_credits_text = f"{int(total_credits)}" if total_credits.is_integer() else f"{total_credits:.1f}"
    print(f"\nTotal credits = {total_credits_text}\n")

    if unavailable_courses:
        print("The following courses are not available:")
        for course_name in unavailable_courses:
            cursor.execute("SELECT Short_Title FROM schedule WHERE Course_Name = ?", (course_name,))
            short_title = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM schedule WHERE Course_Name = ? AND Status = 'P'", (course_name,))
            pending_sections_count = cursor.fetchone()[0]
            pending_sections_text = f"This course has {pending_sections_count} pending sections" if pending_sections_count > 0 else "All sections are full and there are no pending sections"
            print(f"{course_name} \"{short_title}\": {pending_sections_text}")
        print()

def print_summary(valid_combinations):
    print("Generated valid schedule combinations:")
    for i, combination in enumerate(valid_combinations, start=1):
        print(f"Option {i}:")
        for section in combination:
            section_name = section["Name"]
            meeting_days = section["Mtg_Days"] if section["Mtg_Days"] != 'nan' else "Online"
            meeting_times = f"{section['STime']} - {section['ETime']}" if section['STime'] != 'nan' and section['ETime'] != 'nan' else ""
            print(f"  {section_name} ({meeting_days} {meeting_times})")
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

    sections_info, section_columns = retrieve_section_info(cursor, selected_courses)
    sections_info, all_sections = process_corequisites(cursor, sections_info, section_columns)
    combinations_without_coreqs = generate_combinations(cursor, sections_info)
    print("Combinations without corequisites:")
    for i, combination in enumerate(combinations_without_coreqs, start=1):
        print(f"Combination {i}:")
        for section, _ in combination:
            print(f"  {section['Name']} ({section['Mtg_Days']} {section['STime']} - {section['ETime']})")
    valid_combinations = validate_combinations_with_coreqs(combinations_without_coreqs, sections_info, cursor)
    print_summary(valid_combinations)

    # Close the connection
    conn.close()
