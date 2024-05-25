# Part of the building process
# Asks for user input (courses and availability), then generates possible combinations
# This does not work quite right:  do not incorporate co-reqs and does not respect user's time availability

import sqlite3
from datetime import datetime
from itertools import product

def retrieve_section_info(cursor, selected_courses):
    sections_info = {}
    for course_name in selected_courses:
        cursor.execute("""
            SELECT Name, Avail_Seats, Printed_Comments, Corequisite, PTECH, STime, ETime, SDate, EDate, Mtg_Days, Method, Credits
            FROM schedule
            WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
        """, (course_name,))
        sections = cursor.fetchall()
        sections_info[course_name] = sections
    return sections_info

def sort_courses_by_sections(sections_info):
    return sorted(sections_info.keys(), key=lambda course: len(sections_info[course]))

def process_corequisites(cursor, corequisite):
    corequisite_sections = []
    if corequisite:
        coreq_sections = corequisite.split(', ')
        for coreq in coreq_sections:
            cursor.execute("""
                SELECT Name, Avail_Seats, Printed_Comments, Corequisite, PTECH, STime, ETime, SDate, EDate, Mtg_Days, Method, Credits
                FROM schedule
                WHERE Name = ? AND Status = 'A' AND Avail_Seats > 0
            """, (coreq,))
            coreq_section = cursor.fetchone()
            if coreq_section:
                corequisite_sections.append(coreq_section)
    return corequisite_sections

def has_conflicts(selected_sections, section, unavailability_blocks):
    if section[5] == 'nan' or section[6] == 'nan':
        return False  # Skip conflict check for sections with missing time

    try:
        section_start = datetime.strptime(section[5], '%I:%M %p').time()
        section_end = datetime.strptime(section[6], '%I:%M %p').time()
    except ValueError:
        return False  # Skip this section if the time format is incorrect

    section_days = section[9].split(', ')

    for day in section_days:
        if day in unavailability_blocks:
            for block in unavailability_blocks[day]:
                block_start = datetime.strptime(block[0], '%I:%M %p').time()
                block_end = datetime.strptime(block[1], '%I:%M %p').time()
                if not (section_end <= block_start or section_start >= block_end):
                    return True

        for selected in selected_sections:
            selected_days = selected[9].split(', ')
            selected_start = datetime.strptime(selected[5], '%I:%M %p').time()
            selected_end = datetime.strptime(selected[6], '%I:%M %p').time()
            if day in selected_days and not (section_end <= selected_start or section_start >= selected_end):
                return True
    return False

def generate_permutations(cursor, all_sections, unavailability_blocks):
    valid_combinations = []

    all_combinations = list(product(*all_sections.values()))
    for combination in all_combinations:
        if not any(has_conflicts([], section, unavailability_blocks) for section in combination):
            valid_combinations.append(combination)

    return valid_combinations

def print_summary(cursor, selected_courses, unavailable_courses, modality_preferences, valid_combinations):
    total_credits = 0
    print("\nYou selected the following courses:")

    for course_name in selected_courses:
        cursor.execute("SELECT Short_Title, Credits, Corequisite FROM schedule WHERE Course_Name = ?", (course_name,))
        course_info = cursor.fetchone()
        if course_info:
            short_title, credits, coreqs = course_info
            total_credits += float(credits)
            coreqs_text = f" (has corequisites: {coreqs})" if coreqs else ""
            credits_text = f"{int(credits)}" if float(credits).is_integer() else f"{float(credits):.1f}"  # display credits as an integer if it is a whole number (4 instead of 4.0)
            print(f"{course_name} \"{short_title}\" {credits_text} credits{coreqs_text}")

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

    print("Valid combinations of available sections:")
    for i, combination in enumerate(valid_combinations, start=1):
        print(f"Option {i}:")
        for section in combination:
            meeting_info = "" if section[10] == 'ONLIN' else f" ({section[9]} {section[5]}-{section[6]})"  # Mtg_Days, STime, ETime
            print(f"  Section: {section[0]} (Seats: {section[1]}, Modality: {section[10]}){meeting_info}")
        print()

def main():
    from availability import get_availability
    from user_input import get_course_names

    db_name = 'schedule.db'

    # Step 1: Get user availability
    availability, unavailability_blocks = get_availability()

    # Step 2: Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Step 3: Get user course selection
    selected_courses, unavailable_courses, modality_preferences = get_course_names(cursor, max_course_number=8)

    # Step 4: Retrieve section info
    sections_info = retrieve_section_info(cursor, selected_courses)

    # Step 5: Sort courses by number of sections
    sorted_courses = sort_courses_by_sections(sections_info)

    # Step 6: Generate valid permutations
    valid_combinations = generate_permutations(cursor, sections_info, unavailability_blocks)

    # Step 7: Print summary
    print_summary(cursor, selected_courses, unavailable_courses, modality_preferences, valid_combinations)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()
