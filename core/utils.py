# core/utils.py

from datetime import time
from typing import List
from .models import BlockedTimeSlot

# This file contains helper functions that can be reused across the project.
def time_to_slot(t: time) -> int:
    """
    Converts a time object (e.g., time(8, 30)) into its corresponding 30-minute slot index.
    For example, 00:00 is slot 0, 00:30 is slot 1, 08:00 is slot 16.

    Args:
        t: A datetime.time object.

    Returns:
        The integer index of the time slot (0-47).
    """
    return t.hour * 2 + t.minute // 30

def is_timeslot_blocked(
    day: str,
    start_slot: int,
    duration: int,
    blocked_slots: List[BlockedTimeSlot]
) -> bool:
    """
    Checks if a given time range for a task conflicts with any of the defined blocked slots.

    Args:
        day: The day to check (e.g., "Monday").
        start_slot: The starting slot index for the task.
        duration: The duration of the task in slots.
        blocked_slots: A list of all BlockedTimeSlot objects.

    Returns:
        True if there is a conflict, False otherwise.
    """
    task_end_slot = start_slot + duration
    for slot in blocked_slots:
        if slot.day == day:
            blocked_start_slot = time_to_slot(slot.start_time)
            blocked_end_slot = time_to_slot(slot.end_time)
            
            # Check for any overlap between the task's time range and the blocked time range.
            # An overlap exists if one range starts before the other one ends.
            if max(start_slot, blocked_start_slot) < min(task_end_slot, blocked_end_slot):
                return True  # Conflict found
    return False  # No conflict