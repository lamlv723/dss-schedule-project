from dataclasses import dataclass, field
from datetime import time
from typing import List

# This file exclusively contains data class definitions for the project's core objects.
# It does not hold any configuration constants, which are now located in config.py.

@dataclass
class Task:
    """
    Represents a single task to be scheduled.
    Using @dataclass to auto-generate __init__, __eq__, etc.
    """
    name: str
    duration: int
    priority: int = 1
    is_work_time: bool = False

    def __repr__(self) -> str:
        """
        Provides a custom, user-defined string representation for the Task object.
        This method is preserved and overrides the default __repr__ from @dataclass.
        """
        time_type = "Trong giờ" if self.is_work_time else "Ngoài giờ"
        return f"Task(Tên: {self.name}, Thời lượng: {self.duration} slot, Loại: {time_type})"

@dataclass
class ScheduledTask:
    """
    Represents a task that has been placed into the schedule.
    It links a Task to a specific day and start time.
    """
    task: Task
    day: str
    start_slot: int

@dataclass
class Schedule:
    """
    Represents a complete schedule, which is a collection of ScheduledTask objects.
    This is equivalent to a "chromosome" in the genetic algorithm.
    """
    # A schedule is defined by the list of tasks placed within it.
    scheduled_tasks: List[ScheduledTask] = field(default_factory=list)
    
    # The fitness score is calculated and assigned by the algorithm.
    fitness: float = -1.0

    def __repr__(self) -> str:
        """

        Provides a simple representation of the Schedule, showing only its fitness score.
        This method is preserved and overrides the default __repr__ from @dataclass.
        """
        return f"Schedule(Fitness: {self.fitness:.2f})"

@dataclass
class BlockedTimeSlot:
    """
    Represents a period of time that is unavailable for scheduling.
    The algorithm will not be allowed to place any tasks within this slot.
    """
    day: str
    start_time: time
    end_time: time