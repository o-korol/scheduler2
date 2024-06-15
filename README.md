# Course Scheduler

This project is a course scheduler that generates valid schedule combinations for students based on their course preferences, availability, and other criteria. It handles corequisites, modality preferences, gaps between classes, and the number of days on campus.

## Files

- `main.py`: The main script that generates and prints valid schedule combinations.
- `user_input.py`: Handles user input for course selection and modality preferences.
- `availability.py`: Handles user input for availability and unavailability times.
- `generate_db.py`:  Handles generating database from master schedule .csv file.  (Assume that the file will be uploaded once per day.)

## Setup

### Prerequisites

- Python 3.x
- SQLite3

### Database Setup

1. Create an SQLite database named `schedule.db`.
2. Populate the database with the appropriate schema and data using `generate_db.py`.

#### Schedule CSV Cleanup and Database Loader

This script cleans up .csv data related to course schedules and loads it into an SQLite database. It is modular and includes improved logging, error handling, and configuration management.

##### Features of generate_db.py

- Clean up column names and data types
- Handle multiple entries in specific columns
- Extract specific information from comments
- Identify sections reserved for cohorted students
- Save cleaned data to a new CSV file
- Load data into an SQLite database

##### Requirements of generate_db.py

- Python 3.x
- pandas
- sqlite3
- re
- logging

##### Installation of generate_db.py

1. Ensure you have Python 3.x installed on your system.
2. Install the required packages using pip:
    ```sh
    pip install pandas
    ```

##### Usage of generate_db.py

1. Place your schedule CSV file in the same directory as the script.
2. Update the `file_name` and `db_name` variables in the `main` function to match your CSV file name and desired SQLite database name.
3. Run the script:
    ```sh
    python generate_db.py
    ```


### Installing Dependencies for main.py

There are no external dependencies for this project beyond Python's standard library.

## Usage

### Running the Scheduler

To run the course scheduler, execute the `main.py` script:

```bash
python main.py
```

## File Descriptions

### main.py
The main script that performs the following tasks:

Connects to the SQLite database.
Retrieves user-selected courses and availability information.
Retrieves section information for the selected courses.
Processes corequisite sections.
Generates all possible combinations of sections.
Validates the combinations considering corequisites and unavailability.
Calculates combined scores for each combination based on modality preferences, days on campus, and gaps.
Prints the valid schedule combinations sorted by combined score.

### user_input.py
Handles user input for course selection and modality preferences:

Prompts the user to enter up to 8 courses.
Checks the availability of each course in the database.
Retrieves available modalities for each course.
Stores the selected courses and modality preferences.
Prints a summary of the selected courses and any unavailable courses.

Functions:
get_course_names(cursor, max_course_number): Retrieves course names and modality preferences from the user.
print_user_input_summary(cursor, selected_courses, unavailable_courses, modality_preferences): Prints a summary of the user's input.

### availability.py
Handles user input for availability and unavailability times:

Prompts the user to enter their availability for each day of the week.
Stores the user's available and unavailable times.
Processes the availability information for use in scheduling.

Functions:
get_availability(): Retrieves availability information from the user.

## Configuration
The config dictionary in main.py allows for customization of the scoring criteria:

config = {
    "weights": {  # how to weigh different scores vs each other (equal weight = 1 for everything)
        "modality": 3,
        "days": 1,
        "gaps": 1
    },  # how to weigh different values within a category
    "preferences": modality_preferences,
    "day_weights": {1: 0, 2: 1, 3: 2, 4: 3, 5: 4},  # 1 day a week = no penalty; 2 days a week = 1 penalty point; etc.
    "gap_weights": {
        "mandatory_break_start": "12:15 PM",  # "mandatory break" is College Hour
        "mandatory_break_end": "1:15 PM",
        "max_allowed_gap": 20  # In minutes
    }
}

