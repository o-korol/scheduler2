# Set up the environment
import sqlite3

# Set the maximum number of courses a user can request
max_course_number = 8

# Connect to the SQLite database
conn = sqlite3.connect('schedule.db')
cursor = conn.cursor()

# Get user input (course selection)
def get_course_names(cursor, max_course_number):
    selected_courses = []
    unavailable_courses = []
    modality_preferences = {}

    print(f"Please enter up to {max_course_number} courses. Hit Enter without typing a course name to finish early.")

    for i in range(1, max_course_number + 1):
        while True:
            course_name = input(f"Course {i} = ").strip().upper()
            if not course_name:
                break

            if course_name in selected_courses:
                print(f"  You have already entered {course_name}. Please enter a different course or hit Enter to finish.")
                continue

            cursor.execute("SELECT DISTINCT Course_Name FROM schedule WHERE Course_Name = ?", (course_name,))
            course = cursor.fetchone()

            if course:
                cursor.execute("""
                    SELECT DISTINCT Method
                    FROM schedule
                    WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
                """, (course_name,))
                modalities = [row[0] for row in cursor.fetchall()]

                if modalities:
                    if len(modalities) == 1:
                        print(f"  This course has only {modalities[0]} sections available. Is that OK? (y/n): ", end="")
                        response = input().strip().lower()
                        if response == 'y':
                            selected_courses.append(course_name)
                            modality_preferences[course_name] = None
                            break
                    else:
                        print(f"  Available modalities for {course_name}: {', '.join(modalities)}")
                        while True:
                            preference = input(f"  Do you have a preference? ({'/'.join(modalities)}/no): ").strip().upper()
                            if preference in modalities or preference == 'NO':
                                if preference == 'NO':
                                    preference = None
                                modality_preferences[course_name] = preference
                                selected_courses.append(course_name)
                                break
                            else:
                                print("  Invalid input. Please enter a valid modality or 'no'.")
                        break
                else:
                    unavailable_courses.append(course_name)
                    print(f"  No sections are available for the course: {course_name}")
            else:
                print("  Course not found in the database. Please enter a valid course name.")

        if not course_name:
            break

    return selected_courses, unavailable_courses, modality_preferences

def print_user_input_summary(cursor, selected_courses, unavailable_courses, modality_preferences):
    print("\nYou selected the following courses:")
    for course_name in selected_courses:
        cursor.execute("SELECT Short_Title, Corequisite FROM schedule WHERE Course_Name = ?", (course_name,))
        course_info = cursor.fetchone()
        if course_info:
            short_title, coreqs = course_info
            coreqs_text = " (has corequisite)" if coreqs else ""
            modality_pref = modality_preferences.get(course_name)
            modality_text = f" (preference: {modality_pref})" if modality_pref else ""
            print(f"{course_name} \"{short_title}\"{modality_text}{coreqs_text}")

    if unavailable_courses:
        print("\nThe following courses are not available:")
        for course_name in unavailable_courses:
            cursor.execute("SELECT Short_Title FROM schedule WHERE Course_Name = ?", (course_name,))
            short_title = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM schedule WHERE Course_Name = ? AND Status = 'P'", (course_name,))
            pending_sections_count = cursor.fetchone()[0]
            pending_sections_text = f"This course has {pending_sections_count} pending sections" if pending_sections_count > 0 else "All sections are full and there are no pending sections"
            print(f"{course_name} \"{short_title}\": {pending_sections_text}")
        print()

def main():
    # Connect to the SQLite database
    conn = sqlite3.connect('schedule.db')
    cursor = conn.cursor()

    selected_courses, unavailable_courses, modality_preferences = get_course_names(cursor, max_course_number)

    # Print user input summary
    print_user_input_summary(cursor, selected_courses, unavailable_courses, modality_preferences)

    # Close the connection
    conn.close()

if __name__ == "__main__":
    main()
