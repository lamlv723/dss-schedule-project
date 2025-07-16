import random
from typing import List, Tuple
from copy import deepcopy

# Import utilities, models, and the updated configs
from .utils import is_timeslot_blocked, time_to_slot
from .models import Task, Schedule, BlockedTimeSlot, ScheduledTask
from . import configs

# ===================================================================
#
# SECTION 1: INITIALIZATION
#
# ===================================================================

def initialize_schedule(
    tasks_to_schedule: List[Task],
    blocked_slots: List[BlockedTimeSlot]
) -> Schedule:
    """
    Creates a single, new, randomly-generated schedule.
    This function ensures the initial schedule is valid by respecting
    task overlaps, work hours, and blocked time slots.
    """
    new_schedule = Schedule()
    tasks = deepcopy(tasks_to_schedule)
    random.shuffle(tasks)

    occupied_slots = {day: [False] * configs.SLOTS_PER_DAY for day in configs.DAYS_OF_WEEK}

    work_start_slot = time_to_slot(configs.WORK_START_TIME)
    work_end_slot = time_to_slot(configs.WORK_END_TIME)

    for task in tasks:
        placed = False
        # Try to place the task for a limited number of attempts to avoid infinite loops
        for _ in range(1000):
            day = random.choice(configs.DAYS_OF_WEEK)
            
            if task.is_work_time:
                if work_end_slot - work_start_slot < task.duration: continue
                start_slot = random.randint(work_start_slot, work_end_slot - task.duration)
            else:
                start_slot = random.randint(0, configs.SLOTS_PER_DAY - task.duration)

            is_occupied = any(occupied_slots[day][start_slot + i] for i in range(task.duration))
            if is_occupied or is_timeslot_blocked(day, start_slot, task.duration, blocked_slots):
                continue

            scheduled_task = ScheduledTask(task=task, day=day, start_slot=start_slot)
            new_schedule.scheduled_tasks.append(scheduled_task)
            for i in range(task.duration):
                occupied_slots[day][start_slot + i] = True
            
            placed = True
            break
        
        if not placed:
            # Handle cases where a task cannot be placed (e.g., not enough free time)
            # For simplicity, we are just noting it here. A more robust solution might raise an error.
            print(f"Warning: Could not place task '{task.name}'. It might be too long or the schedule is too constrained.")

    return new_schedule

# ===================================================================
#
# SECTION 2: FITNESS CALCULATION (REWRITTEN)
#
# ===================================================================

def calculate_fitness(schedule: Schedule, blocked_slots: List[BlockedTimeSlot]) -> float:
    """
    Calculates the fitness score of a given schedule based on multiple criteria.
    - Higher score is better.
    - This is the core logic that guides the evolution process.
    """
    if not schedule.scheduled_tasks:
        return 0.0

    score = 1000.0  # Start with a base score to subtract penalties from
    
    # Sort tasks for easier processing of gaps and day spans
    sorted_tasks = sorted(schedule.scheduled_tasks, key=lambda x: (configs.DAYS_OF_WEEK.index(x.day), x.start_slot))

    # --- Criterion 1: Priority Weighting ---
    # Heavily reward scheduling high-priority tasks early.
    total_slots = len(configs.DAYS_OF_WEEK) * configs.SLOTS_PER_DAY
    for st in sorted_tasks:
        priority_weight = (configs.TOTAL_PRIORITY_LEVELS - st.task.priority) ** 2  # Exponential weight
        time_bonus = total_slots - (configs.DAYS_OF_WEEK.index(st.day) * configs.SLOTS_PER_DAY + st.start_slot)
        score += priority_weight * time_bonus * 0.1

    # --- Criterion 2: Gap Penalty ---
    # Penalize for gaps between tasks on the same day > 30 mins.
    for i in range(len(sorted_tasks) - 1):
        current_task = sorted_tasks[i]
        next_task = sorted_tasks[i+1]
        if current_task.day == next_task.day:
            gap = next_task.start_slot - (current_task.start_slot + current_task.task.duration)
            if gap > 1:  # Penalize gaps > 1 slot (30 minutes)
                score -= gap * 5 # A moderate penalty for each empty slot

    # --- Criterion 3: Day Spill-over Penalty ---
    # Penalize for using more days than necessary.
    unique_days_used = len(set(st.day for st in sorted_tasks))
    if unique_days_used > 1:
        score -= (unique_days_used - 1) * 100 # Heavy penalty for each extra day

    schedule.fitness = score
    return score

# ===================================================================
#
# SECTION 3: GENETIC OPERATORS (REWRITTEN)
#
# ===================================================================

def selection(population: List[Schedule]) -> List[Schedule]:
    """
    Selects the best individuals from the population to be parents for the next generation.
    Uses Tournament Selection.
    """
    selected = []
    pop_size = len(population)
    for _ in range(pop_size):
        tournament_size = max(2, int(pop_size * 0.05))
        participants = random.sample(population, tournament_size)
        winner = max(participants, key=lambda s: s.fitness)
        selected.append(winner)
    return selected

def crossover(parent1: Schedule, parent2: Schedule) -> Schedule:
    """
    Combines two parent schedules to create a child schedule.
    This version uses a simple single-point crossover on the list of scheduled tasks.
    """
    child = Schedule()
    # Ensure tasks are in a consistent order before crossover
    p1_tasks = sorted(parent1.scheduled_tasks, key=lambda x: x.task.name)
    p2_tasks = sorted(parent2.scheduled_tasks, key=lambda x: x.task.name)

    crossover_point = random.randint(1, len(p1_tasks) - 1)
    
    # Take the first part from parent1 and the second from parent2
    child.scheduled_tasks = deepcopy(p1_tasks[:crossover_point]) + deepcopy(p2_tasks[crossover_point:])
    
    # Basic conflict resolution: If tasks overlap, the schedule's fitness will be very low,
    # and it will likely be eliminated by natural selection. A more advanced crossover
    # would involve a repair mechanism here.
    return child

def mutate(schedule: Schedule, blocked_slots: List[BlockedTimeSlot]) -> Schedule:
    """
    Applies a random change to a schedule to introduce new genetic material.
    This mutation respects all placement rules (work hours, no overlaps, no blocked slots).
    """
    if not schedule.scheduled_tasks:
        return schedule

    mutated_schedule = deepcopy(schedule)
    
    # Choose a random task to move
    task_to_move_idx = random.randrange(len(mutated_schedule.scheduled_tasks))
    task_to_move = mutated_schedule.scheduled_tasks.pop(task_to_move_idx)

    # Re-build the occupied slots map for the schedule *without* the task to move
    occupied_slots = {day: [False] * configs.SLOTS_PER_DAY for day in configs.DAYS_OF_WEEK}
    for st in mutated_schedule.scheduled_tasks:
        for i in range(st.task.duration):
            occupied_slots[st.day][st.start_slot + i] = True

    # Find a new valid position for the moved task (similar to initialize)
    work_start_slot = time_to_slot(configs.WORK_START_TIME)
    work_end_slot = time_to_slot(configs.WORK_END_TIME)
    
    placed = False
    for _ in range(500): # Try 500 times to find a new spot
        day = random.choice(configs.DAYS_OF_WEEK)
        
        if task_to_move.task.is_work_time:
            if work_end_slot - work_start_slot < task_to_move.task.duration: continue
            start_slot = random.randint(work_start_slot, work_end_slot - task_to_move.task.duration)
        else:
            start_slot = random.randint(0, configs.SLOTS_PER_DAY - task_to_move.task.duration)

        is_occupied = any(occupied_slots[day][start_slot + i] for i in range(task_to_move.task.duration))
        if is_occupied or is_timeslot_blocked(day, start_slot, task_to_move.task.duration, blocked_slots):
            continue

        # Place the task in its new valid spot
        task_to_move.day = day
        task_to_move.start_slot = start_slot
        mutated_schedule.scheduled_tasks.append(task_to_move)
        placed = True
        break

    if not placed:
        # If a new spot couldn't be found, return the original, un-mutated schedule
        return schedule
        
    return mutated_schedule

# ===================================================================
#
# SECTION 4: MAIN ALGORITHM LOOP
#
# ===================================================================

def run_genetic_algorithm(
    tasks_to_schedule: List[Task],
    blocked_slots: List[BlockedTimeSlot],
    population_size: int,
    generations: int,
    mutation_rate: float
) -> Schedule:
    """
    The main function that orchestrates the genetic algorithm.
    """
    # Initialize the population
    population = [initialize_schedule(tasks_to_schedule, blocked_slots) for _ in range(population_size)]

    for gen in range(generations):
        # --- Evaluation ---
        # Calculate fitness for each schedule that hasn't been evaluated yet
        for schedule in population:
            if schedule.fitness == -1.0: # Only calculate if not already set
                calculate_fitness(schedule, blocked_slots)
        
        # --- Elitism ---
        # Sort the population by fitness (higher is better) and keep the top 10%
        population.sort(key=lambda s: s.fitness, reverse=True)
        elitism_count = max(2, int(population_size * 0.1))
        next_generation = population[:elitism_count]
        
        # --- Reproduction ---
        # Select parents for the new generation
        selected_parents = selection(population)
        
        # Create new individuals (children)
        while len(next_generation) < population_size:
            p1, p2 = random.sample(selected_parents, 2)
            child = crossover(p1, p2)
            if random.random() < mutation_rate:
                child = mutate(child, blocked_slots)
            
            # The child's fitness needs to be recalculated
            child.fitness = -1.0
            next_generation.append(child)
        
        population = next_generation
        
        best_fitness_in_gen = population[0].fitness
        print(f"Thế hệ {gen + 1}/{generations} - Fitness tốt nhất: {best_fitness_in_gen:.2f}")

    # Return the best individual from the final population
    best_schedule = max(population, key=lambda s: s.fitness)
    return best_schedule