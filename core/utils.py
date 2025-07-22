import math
import random
from typing import List, Tuple, Optional
from datetime import time
from .models import Task, BlockedTimeSlot
from . import configs

# ==============================================================================
# This is the complete and unified utility file.
# It contains all helper functions for time conversion, task processing,
# and schedule validation.
# ==============================================================================

def time_to_slot(t: time) -> int:
    """
    Converts a datetime.time object to its corresponding slot index.
    
    The calculation is based on the SLOT_DURATION_MINUTES defined in configs.
    For example, with 30-minute slots, 8:00 AM becomes slot 16.
    """
    total_minutes = t.hour * 60 + t.minute
    return total_minutes // configs.SLOT_DURATION_MINUTES


def task_duration_to_slots(duration_minutes: int) -> int:
    """
    Calculates how many time slots a task occupies.

    Uses ceiling to ensure enough space is allocated for the task.
    e.g., a 45-min task in a 30-min slot system will occupy ceil(45/30) = 2 slots.
    """
    num_slots = duration_minutes / configs.SLOT_DURATION_MINUTES
    return math.ceil(num_slots)


def is_time_blocked(day: int, slot: int, blocked_slots_list: List[BlockedTimeSlot]) -> bool:
    """
    Checks if a specific time slot on a given day is blocked.

    Iterates through the list of predefined blocked time slots (like lunch, sleep)
    to see if the given slot falls within any of those ranges.
    """
    for blocked in blocked_slots_list:
        if blocked.day == day and blocked.start_time <= slot < blocked.end_time:
            return True
    return False


def find_valid_spot_for_task(task: Task, schedule_matrix: List[List[Optional[Task]]]) -> Optional[Tuple[int, int]]:
    """
    Attempts to find a random, valid (unoccupied and not blocked) spot for a task.
    
    This is a helper for creating the initial population. It tries a fixed
    number of times to place a task randomly.
    """
    task_slots = task_duration_to_slots(task.duration)
    
    # Try to place the task a certain number of times before giving up
    for _ in range(100): # 100 attempts to find a spot
        day = random.randint(0, configs.DAYS_IN_SCHEDULE - 1)
        start_slot = random.randint(0, configs.SLOTS_PER_DAY - task_slots)
        
        is_valid = True
        for i in range(task_slots):
            slot_to_check = start_slot + i
            # Check if the slot is already taken or if it's a blocked time
            if schedule_matrix[day][slot_to_check] is not None or \
               is_time_blocked(day, slot_to_check, configs.BLOCKED_TIME_SLOTS):
                is_valid = False
                break
        
        if is_valid:
            return day, start_slot
            
    return None # Return None if no valid spot was found


def expand_tasks_by_frequency(tasks: List[Task]) -> List[Task]:
    """
    Expands tasks with a frequency > 1 into individual task instances.

    A task "Workout" with frequency=3 becomes three separate tasks.
    This is necessary for the genetic algorithm to process each instance individually.
    """
    expanded_list: List[Task] = []
    for task in tasks:
        if task.frequency <= 1:
            expanded_list.append(task)
        else:
            for i in range(1, task.frequency + 1):
                new_task_instance = Task(
                    name=f"{task.name} {i}/{task.frequency}",
                    duration=task.duration,
                    priority=task.priority,
                    frequency=1,  # Each new instance has a frequency of 1
                    parent_task=task.name
                )
                expanded_list.append(new_task_instance)
    return expanded_list