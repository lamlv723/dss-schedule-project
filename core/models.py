from dataclasses import dataclass, field
from typing import List, Optional

# This file defines the data structures for the application using Python's
# built-in dataclasses. This approach is lightweight and perfect for
# applications that do not require a database for persistence.

@dataclass
class Task:
    """
    Represents a task definition or a template for a task.
    This is the "blueprint" of a task, defined by the user.
    """
    # A unique identifier for the task, can be its name or a generated ID.
    name: str
    
    # The duration of the task in minutes.
    duration: int
    
    # The priority level of the task (e.g., 1-5, where 5 is the highest).
    priority: int = 1
    
    # The number of times this task should appear in the schedule.
    frequency: int = 1
    
    # For tasks generated from frequency > 1, this stores the original task's name.
    parent_task: Optional[str] = None

@dataclass
class BlockedTimeSlot:
    """
    Represents a time slot that is unavailable for scheduling.
    Used for fixed events like lunch, sleep, or appointments.
    """
    # A descriptive name for the blocked slot (e.g., "Lunch Break").
    reason: str

    # The day of the week for the blocked slot (0 for Monday, etc.).
    day: int

    # The starting time slot to block.
    start_time: int
    
    # The ending time slot to block.
    end_time: int


@dataclass
class ScheduledTask:
    """
    Represents a specific instance of a Task that has been placed on the schedule.
    This is the actual "event" in the calendar.
    """
    # The original task object that this event is based on.
    task: Task
    
    # The day in the schedule where the task is placed (0 for Monday, etc.).
    day: int
    
    # The starting time slot for the task on the specified day.
    start_time: int


@dataclass
class Schedule:
    """
    Represents a single, complete schedule for a given period (e.g., a week).
    It acts as a container for all the 'ScheduledTask' instances.
    """
    # A list of all tasks that have been successfully placed on this schedule.
    # It defaults to an empty list when a new Schedule is created.
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)