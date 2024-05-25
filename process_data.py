from datetime import datetime

# Process course sections against user availability
def process_course_sections(cursor, selected_courses, unavailability_blocks):
    sections_available = {}

    for course_name in selected_courses:
        cursor.execute("""
            SELECT Course_Name, Short_Title, STime, ETime, Status, Avail_Seats, Method, Printed_Comments, Corequisite
            FROM schedule
            WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
        """, (course_name,))
        sections = cursor.fetchall()

        sections_available[course_name] = {'inside': 0, 'outside': 0}

        for section in sections:
            start_time, end_time = section[2], section[3]
            if start_time and end_time and start_time != 'nan' and end_time != 'nan':
                try:
                    section_start = datetime.strptime(start_time, '%I:%M %p').time()
                    section_end = datetime.strptime(end_time, '%I:%M %p').time()
                except ValueError:
                    continue

                conflicts = any(
                    section_start < datetime.strptime(block[1], '%I:%M %p').time() and section_end > datetime.strptime(block[0], '%I:%M %p').time()
                    for day, blocks in unavailability_blocks.items()
                    for block in blocks
                )
                if conflicts:
                    sections_available[course_name]['outside'] += 1
                else:
                    sections_available[course_name]['inside'] += 1
            else:
                sections_available[course_name]['inside'] += 1  # Online classes or those with no specific meeting times

    return sections_available

# Function to print the summary of course selections and availability
def print_summary(cursor, selected_courses, unavailable_courses, modality_preferences, sections_available):
    total_credits = 0
    print("\nYou selected the following courses:")

    for course_name in selected_courses:
        cursor.execute("SELECT Short_Title, Credits, Corequisite FROM schedule WHERE Course_Name = ?", (course_name,))
        course_info = cursor.fetchone()
        if course_info:
            short_title, credits, coreqs = course_info
            total_credits += credits
            coreqs_text = f" (has corequisites)" if coreqs else ""
            credits_text = f"{int(credits)}" if credits.is_integer() else f"{credits:.1f}"  # Display credits as an integer if it is a whole number (4 instead of 4.0)
            modality_text = f" (modality: {modality_preferences[course_name]})" if modality_preferences.get(course_name) else " (no modality preference)"
            print(f"{course_name} \"{short_title}\" {credits_text} credits{coreqs_text}{modality_text}")
            print(f"  Sections available within your time: {sections_available[course_name]['inside']}")
            print(f"  Sections available outside your time: {sections_available[course_name]['outside']}")

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

if __name__ == "__main__":
    # For testing purposes, this section can be used to manually set variables or directly invoke functions
    pass
