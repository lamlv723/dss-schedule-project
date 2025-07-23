# config/app_config.py

# Duration of each time slot in minutes
TIME_SLOT_DURATION = 30

# Number of time slots in a day (24 hours * 60 minutes / TIME_SLOT_DURATION)
SLOTS_PER_DAY = int((24 * 60) / TIME_SLOT_DURATION)

# Total number of days in the schedule
DAYS_IN_SCHEDULE = 7

# Total time slots in the schedule
TOTAL_TIME_SLOTS = SLOTS_PER_DAY * DAYS_IN_SCHEDULE

# Default blocked times if none are provided by the user
DEFAULT_BLOCKED_TIMES = """
# Sleep (Daily 11 PM to 7 AM)
daily 23:00-07:00

# Lunch (Daily 12:30 PM to 1:30 PM)
daily 12:30-13:30

# Dinner (Daily 7 PM to 8 PM)
daily 19:00-20:00
"""
