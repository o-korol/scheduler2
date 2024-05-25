# This code is a part of build-up to schedule generation
# This part checks whether we can successfully retrieve section information
import sqlite3

def retrieve_section_info(cursor, selected_courses):
    sections_info = {}
    for course_name in selected_courses:
        cursor.execute("""
            SELECT Name, Avail_Seats, Printed_Comments, Corequisite, PTECH, STime, ETime, SDate, EDate, Mtg_Days, Method
            FROM schedule
            WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
        """, (course_name,))
        sections = cursor.fetchall()
        sections_info[course_name] = sections
    return sections_info

def sort_courses_by_sections(sections_info):
    return sorted(sections_info.keys(), key=lambda course: len(sections_info[course]))

def main():
    db_name = 'schedule.db'

    # Connect to the SQLite database
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()

    # Example course list (this would come from user input, but for now it is hard-coded)
    selected_courses = ["BIO-172", "MAT-143"]

    # Retrieve section info
    sections_info = retrieve_section_info(cursor, selected_courses)
    print("Sections Info:")
    for course, sections in sections_info.items():
        print(f"{course}: {sections}")

    # Sort courses by number of sections
    sorted_courses = sort_courses_by_sections(sections_info)
    print("Sorted Courses:")
    print(sorted_courses)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()
