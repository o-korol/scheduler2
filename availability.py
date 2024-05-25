import re
from datetime import datetime

def parse_time(time_str):
    '''Parses the time string and converts it to the standard format.'''
    time_str = time_str.strip().lower()
    if re.match(r'^\d{1,2}$', time_str):
        time_str += ' am'
    try:
        return datetime.strptime(time_str, '%I %p').strftime('%I:%M %p')
    except ValueError:
        return None

def get_time_input(prompt):
    '''Prompts the user for time input and ensures valid format.'''
    while True:
        time_input = input(prompt).strip().lower()
        if re.match(r'^\d{1,2}$', time_input):
            while True:
                am_pm = input("Is that am or pm? (am/pm): ").strip().lower()
                if am_pm in ['am', 'pm']:
                    time_input += f" {am_pm}"
                    break
                else:
                    print("Invalid input. Please enter 'am' or 'pm'.")
        time = parse_time(time_input)
        if time:
            return time
        else:
            print("Invalid time format. Please try again.")

def get_days_not_available():
    '''Prompts the user for days they are not available and parses the input.'''
    while True:
        days_not_available = input("Which days are NOT available? (M, T, W, TH, F, S) ").strip().upper()
        parsed_days = []
        day_mapping = {'M': 'Mon', 'T': 'Tue', 'W': 'Wed', 'TH': 'Thu', 'F': 'Fri', 'S': 'Sat'}
        days_not_available = re.findall(r'\bM\b|\bT\b|\bW\b|\bTH\b|\bF\b|\bS\b', days_not_available)
        for day in days_not_available:
            if day in day_mapping:
                parsed_days.append(day_mapping[day])
        if parsed_days:
            return parsed_days
        else:
            print("Invalid input. Please enter days using their abbreviations (e.g., M, T, W, TH, F, S).")

def get_availability():
    '''Prompts the user for their availability and constructs availability and unavailability blocks.'''
    print("Next, we will ask you a few questions about your availability.")
    available_all_days = input("Are you available Mon-Fri and Sat if needed? (y/n): ").strip().lower()

    availability = {}
    not_available_days = []

    if available_all_days == 'y':
        # User is available all days
        start_time = get_time_input("On Monday, what time can you start? (e.g., 08:00 AM): ")
        end_time = get_time_input("On Monday, what time can you finish? (e.g., 08:00 AM): ")
        same_time_all_days = input("Is your time availability the same on the other days of the week? (y/n): ").strip().lower()

        days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        if same_time_all_days == 'y':
            for day in days_of_week:
                availability[day] = (start_time, end_time)
        else:
            for day in days_of_week:
                start_time = get_time_input(f"On {day}, what time can you start? (e.g., 08:00 AM): ")
                end_time = get_time_input(f"On {day}, what time can you finish? (e.g., 08:00 AM): ")
                availability[day] = (start_time, end_time)
    else:
        # User is not available all days
        not_available_days = get_days_not_available()
        available_days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for day in not_available_days:
            if day in available_days:
                available_days.remove(day)

        if available_days:
            start_time = get_time_input(f"On {available_days[0]}, what time can you start? (e.g., 08:00 AM): ")
            end_time = get_time_input(f"On {available_days[0]}, what time can you finish? (e.g., 08:00 AM): ")
            availability[available_days[0]] = (start_time, end_time)
            same_time_all_days = input("Is your time availability the same on the other available days? (y/n): ").strip().lower()

            if same_time_all_days == 'y':
                for day in available_days[1:]:
                    availability[day] = (start_time, end_time)
            else:
                for day in available_days[1:]:
                    start_time = get_time_input(f"On {day}, what time can you start? (e.g., 08:00 AM): ")
                    end_time = get_time_input(f"On {day}, what time can you finish? (e.g., 08:00 AM): ")
                    availability[day] = (start_time, end_time)

    unavailability_blocks = {}
    for day, times in availability.items():
        start_time, end_time = times
        unavailability_blocks[day] = [
            ('12:00 AM', start_time),
            (end_time, '11:59 PM')
        ]

    for day in not_available_days:
        unavailability_blocks[day] = [('12:00 AM', '11:59 PM')]

    return availability, unavailability_blocks

def print_availability(availability, unavailability_blocks):
    '''Prints the user's availability.'''
    print("\nYour availability is:")
    for day, times in availability.items():
        start_time, end_time = times
        print(f"{day}: {start_time} to {end_time}")

    # Uncomment the following lines if you want to print unavailability_blocks for debugging
    # print("\nUnavailability blocks:")
    # for day, blocks in unavailability_blocks.items():
    #     print(f"{day}: {blocks}")

if __name__ == "__main__":
    availability, unavailability_blocks = get_availability()
    print_availability(availability, unavailability_blocks)
