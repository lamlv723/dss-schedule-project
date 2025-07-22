from datetime import time
from typing import List
from .models import BlockedTimeSlot
from . import utils # Import the entire utils module

# --- Genetic Algorithm Parameters ---
POPULATION_SIZE: int = 50
NUM_GENERATIONS: int = 100
MUTATION_RATE: float = 0.01

# --- Schedule-related Constants ---
DAYS_IN_SCHEDULE: int = 7
SLOT_DURATION_MINUTES: int = 30
SLOTS_PER_DAY: int = (24 * 60) // SLOT_DURATION_MINUTES

# --- Blocked Time Slots ---
# Define periods where no tasks can be scheduled.
# This uses the helper function for readability.
# Day mapping: 0=Monday, 1=Tuesday, ..., 6=Sunday
BLOCKED_TIME_SLOTS: List[BlockedTimeSlot] = [
    # Block time for sleep every day from midnight to 8 AM
    BlockedTimeSlot(
        reason="Sleep", 
        day=0, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(8, 0))
    ),
    BlockedTimeSlot(
        reason="Sleep", 
        day=1, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(8, 0))
    ),
    BlockedTimeSlot(
        reason="Sleep", 
        day=2, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(8, 0))
    ),
    BlockedTimeSlot(
        reason="Sleep", 
        day=3, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(8, 0))
    ),
    BlockedTimeSlot(
        reason="Sleep", 
        day=4, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(8, 0))
    ),
    # Weekends might have different sleeping patterns, but we keep it simple here
    BlockedTimeSlot(
        reason="Sleep", 
        day=5, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(9, 0))
    ),
    BlockedTimeSlot(
        reason="Sleep", 
        day=6, 
        start_time=utils.time_to_slot(time(0, 0)), 
        end_time=utils.time_to_slot(time(9, 0))
    ),

    # Block lunch break on weekdays from 12:00 to 13:00
    BlockedTimeSlot(
        reason="Lunch", 
        day=0, 
        start_time=utils.time_to_slot(time(12, 0)), 
        end_time=utils.time_to_slot(time(13, 0))
    ),
    BlockedTimeSlot(
        reason="Lunch", 
        day=1, 
        start_time=utils.time_to_slot(time(12, 0)), 
        end_time=utils.time_to_slot(time(13, 0))
    ),
    BlockedTimeSlot(
        reason="Lunch", 
        day=2, 
        start_time=utils.time_to_slot(time(12, 0)), 
        end_time=utils.time_to_slot(time(13, 0))
    ),
    BlockedTimeSlot(
        reason="Lunch", 
        day=3, 
        start_time=utils.time_to_slot(time(12, 0)), 
        end_time=utils.time_to_slot(time(13, 0))
    ),
    BlockedTimeSlot(
        reason="Lunch", 
        day=4, 
        start_time=utils.time_to_slot(time(12, 0)), 
        end_time=utils.time_to_slot(time(13, 0))
    ),
]