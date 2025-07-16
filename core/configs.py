from datetime import time
from .models import BlockedTimeSlot

# =================== SCHEDULING ENVIRONMENT CONSTANTS ===================
# These constants define the fundamental rules of the scheduling world.
# ----------------------------------------------------------------------
# Time representation
SLOTS_PER_DAY = 48  # 48 slots of 30 minutes each for a 24-hour day
DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Definition of working hours
WORK_START_TIME = time(8, 0)
WORK_END_TIME = time(17, 0)

# The total number of priority levels. Used in the fitness function.
TOTAL_PRIORITY_LEVELS = 5

# =================== GENETIC ALGORITHM PARAMETERS ===================
# All tunable parameters for the genetic algorithm are defined here.
# ----------------------------------------------------------------------
POPULATION_SIZE = 200
GENERATIONS = 500
MUTATION_RATE = 0.1

# ===================== BLOCKED TIME SLOTS =======================
# Define any time slots that are unavailable for scheduling.
# ----------------------------------------------------------------------
blocked_slots = [
    # Block sleep time from 00:00 to 07:00 every day
    BlockedTimeSlot(day="Monday", start_time=time(0, 0), end_time=time(8, 0)),
    BlockedTimeSlot(day="Tuesday", start_time=time(0, 0), end_time=time(8, 0)),
    BlockedTimeSlot(day="Wednesday", start_time=time(0, 0), end_time=time(8, 0)),
    BlockedTimeSlot(day="Thursday", start_time=time(0, 0), end_time=time(8, 0)),
    BlockedTimeSlot(day="Friday", start_time=time(0, 0), end_time=time(8, 0)),
    BlockedTimeSlot(day="Saturday", start_time=time(0, 0), end_time=time(8, 0)),
    BlockedTimeSlot(day="Sunday", start_time=time(0, 0), end_time=time(8, 0)),

    # Block a fixed class on Wednesday evening
    BlockedTimeSlot(day="Wednesday", start_time=time(19, 0), end_time=time(20, 30)),
]