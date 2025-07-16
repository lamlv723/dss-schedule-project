import random
from datetime import time
from typing import List, Tuple

# Import models and configs as they are needed by the helper functions
from .models import BlockedTimeSlot, Task
from . import configs

# This file contains helper functions that can be reused across the project.

def time_to_slot(t: time) -> int:
    """Converts a time object into its corresponding 30-minute slot index."""
    return t.hour * 2 + t.minute // 30

def is_timeslot_blocked(
    day: str,
    start_slot: int,
    duration: int,
    blocked_slots: List[BlockedTimeSlot]
) -> bool:
    """Checks if a given time range conflicts with any defined blocked slots."""
    task_end_slot = start_slot + duration
    for slot in blocked_slots:
        if slot.day == day:
            blocked_start_slot = time_to_slot(slot.start_time)
            blocked_end_slot = time_to_slot(slot.end_time)
            if max(start_slot, blocked_start_slot) < min(task_end_slot, blocked_end_slot):
                return True
    return False

def find_valid_spot_for_task(
    task: Task,
    occupied_slots: dict,
    blocked_slots: List[BlockedTimeSlot]
) -> Tuple[str, int] | None:
    """
    A robust helper function to find a single valid placement for a task.
    This respects all rules: work hours, personal hours, overlaps, and blocked slots.
    """
    work_start_slot = time_to_slot(configs.WORK_START_TIME)
    work_end_slot = time_to_slot(configs.WORK_END_TIME)
    
    # Create a shuffled list of days to try, to ensure randomness
    days_to_try = configs.DAYS_OF_WEEK[:]
    random.shuffle(days_to_try)

    for day in days_to_try:
        # Create a shuffled list of possible start slots for the current day
        possible_start_slots = list(range(configs.SLOTS_PER_DAY - task.duration + 1))
        random.shuffle(possible_start_slots)

        for start_slot in possible_start_slots:
            # Rule 1: Check Work/Personal Time Constraint
            is_in_work_hours = work_start_slot <= start_slot < work_end_slot
            if task.is_work_time and not is_in_work_hours:
                continue # Work task must be inside work hours
            if not task.is_work_time and is_in_work_hours:
                continue # Personal task must be outside work hours

            # Rule 2: Check for Overlap with other Tasks
            if any(occupied_slots[day][start_slot + i] for i in range(task.duration)):
                continue

            # Rule 3: Check for Conflict with Blocked Slots
            if is_timeslot_blocked(day, start_slot, task.duration, blocked_slots):
                continue
            
            # If all checks pass, we found a valid spot
            return day, start_slot

    return None # Return None if no valid spot was found

def calculate_adaptive_rate(
    fitness_value: float,
    max_fitness: float,
    avg_fitness: float,
    k_value: float
) -> float:
    """
    Calculates an adaptive rate for crossover or mutation based on fitness values.
    This formula is inspired by the work of Srinivas and Patnaik (1994).

    Args:
        fitness_value: The fitness of the individual chromosome.
        max_fitness: The maximum fitness in the current population.
        avg_fitness: The average fitness of the current population.
        k_value: A constant factor (k1 for crossover, k2 for mutation).

    Returns:
        The calculated adaptive rate. Returns k_value if the individual is average or below.
    """
    if fitness_value > avg_fitness:
        # For individuals better than average, the rate is lower to preserve good genes.
        return k_value * (max_fitness - fitness_value) / (max_fitness - avg_fitness)
    else:
        # For average or below-average individuals, the rate is higher to encourage exploration.
        return k_value