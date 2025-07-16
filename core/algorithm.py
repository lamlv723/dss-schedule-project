import random
from typing import List
from copy import deepcopy

# Import utilities, models, and configs
from .utils import is_timeslot_blocked, time_to_slot, find_valid_spot_for_task
from .models import Task, Schedule, BlockedTimeSlot, ScheduledTask
from . import configs

# ===================================================================
#
# SECTION 1: INITIALIZATION & MUTATION (LOGIC REFINED)
#
# ===================================================================
def initialize_schedule(
    tasks_to_schedule: List[Task],
    blocked_slots: List[BlockedTimeSlot]
) -> Schedule:
    """Creates a single, new, randomly-generated, and valid schedule."""
    new_schedule = Schedule()
    tasks = deepcopy(tasks_to_schedule)
    random.shuffle(tasks)
    occupied_slots = {day: [False] * configs.SLOTS_PER_DAY for day in configs.DAYS_OF_WEEK}

    for task in tasks:
        spot = find_valid_spot_for_task(task, occupied_slots, blocked_slots)
        if spot:
            day, start_slot = spot
            new_schedule.scheduled_tasks.append(ScheduledTask(task=task, day=day, start_slot=start_slot))
            for i in range(task.duration):
                occupied_slots[day][start_slot + i] = True
        else:
            print(f"Warning (Initialization): Could not place task '{task.name}'.")
            
    return new_schedule

# ===================================================================
#
# SECTION 2: FITNESS CALCULATION (UNCHANGED)
#
# ===================================================================

def calculate_fitness(schedule: Schedule, blocked_slots: List[BlockedTimeSlot]) -> float:
    # This function is assumed to be correct from the previous step.
    # We will refine it later if needed.
    if not schedule.scheduled_tasks: return 0.0
    score = 1000.0
    sorted_tasks = sorted(schedule.scheduled_tasks, key=lambda x: (configs.DAYS_OF_WEEK.index(x.day), x.start_slot))
    total_slots = len(configs.DAYS_OF_WEEK) * configs.SLOTS_PER_DAY
    for st in sorted_tasks:
        priority_weight = (configs.TOTAL_PRIORITY_LEVELS - st.task.priority) ** 2
        time_bonus = total_slots - (configs.DAYS_OF_WEEK.index(st.day) * configs.SLOTS_PER_DAY + st.start_slot)
        score += priority_weight * time_bonus * 0.1
    for i in range(len(sorted_tasks) - 1):
        current_task, next_task = sorted_tasks[i], sorted_tasks[i+1]
        if current_task.day == next_task.day:
            gap = next_task.start_slot - (current_task.start_slot + current_task.task.duration)
            if gap > 1: score -= gap * 5
    unique_days_used = len(set(st.day for st in sorted_tasks))
    if unique_days_used > 1: score -= (unique_days_used - 1) * 100
    schedule.fitness = score
    return score

# ===================================================================
#
# SECTION 3: GENETIC OPERATORS (CROSSOVER REPLACED, MUTATE REFINED)
#
# ===================================================================

def selection(population: List[Schedule]) -> List[Schedule]:
    """Selects parents using Tournament Selection."""
    selected = []
    for _ in range(len(population)):
        participants = random.sample(population, k=max(2, int(len(population) * 0.05)))
        winner = max(participants, key=lambda s: s.fitness)
        selected.append(winner)
    return selected

def crossover(parent1: Schedule, parent2: Schedule, blocked_slots: List[BlockedTimeSlot]) -> Schedule:
    """
    Creates a new, valid child schedule by combining two parents.
    This is an advanced crossover operator with a repair mechanism.
    """
    child = Schedule()
    
    # --- Step 1: Inherit a valid subset of tasks from Parent 1 ---
    tasks_from_p1 = []
    # Take about half of the tasks from parent1
    for scheduled_task in parent1.scheduled_tasks:
        if random.random() < 0.5:
            tasks_from_p1.append(deepcopy(scheduled_task))
    
    child.scheduled_tasks = tasks_from_p1
    
    # --- Step 2: Build a list of tasks that still need to be scheduled ---
    scheduled_task_names = {st.task.name for st in child.scheduled_tasks}
    tasks_to_schedule = [
        st.task for st in parent2.scheduled_tasks 
        if st.task.name not in scheduled_task_names
    ]
    random.shuffle(tasks_to_schedule)

    # --- Step 3: Repair the child by placing the remaining tasks intelligently ---
    occupied_slots = {day: [False] * configs.SLOTS_PER_DAY for day in configs.DAYS_OF_WEEK}
    for st in child.scheduled_tasks:
        for i in range(st.task.duration):
            occupied_slots[st.day][st.start_slot + i] = True
    
    for task in tasks_to_schedule:
        spot = find_valid_spot_for_task(task, occupied_slots, blocked_slots)
        if spot:
            day, start_slot = spot
            child.scheduled_tasks.append(ScheduledTask(task=task, day=day, start_slot=start_slot))
            for i in range(task.duration):
                occupied_slots[day][start_slot + i] = True
        else:
            print(f"Warning (Crossover): Could not place task '{task.name}'.")

    return child


def mutate(schedule: Schedule, blocked_slots: List[BlockedTimeSlot]) -> Schedule:
    """
    Applies a random, valid change to a schedule.
    It moves a single task to a new, valid random position.
    """
    if len(schedule.scheduled_tasks) < 2:
        return schedule

    mutated_schedule = deepcopy(schedule)
    
    # 1. Pick a random task to move and remove it
    task_to_move_idx = random.randrange(len(mutated_schedule.scheduled_tasks))
    task_to_move = mutated_schedule.scheduled_tasks.pop(task_to_move_idx)

    # 2. Re-build the occupied slots map without the moved task
    occupied_slots = {day: [False] * configs.SLOTS_PER_DAY for day in configs.DAYS_OF_WEEK}
    for st in mutated_schedule.scheduled_tasks:
        for i in range(st.task.duration):
            occupied_slots[st.day][st.start_slot + i] = True

    # 3. Find a new valid spot for the task
    spot = find_valid_spot_for_task(task_to_move.task, occupied_slots, blocked_slots)

    if spot:
        # 4. If a spot is found, add the task back in the new position
        day, start_slot = spot
        mutated_schedule.scheduled_tasks.append(ScheduledTask(task=task_to_move.task, day=day, start_slot=start_slot))
        return mutated_schedule
    else:
        # If no new spot could be found, return the original schedule to avoid creating an invalid one
        return schedule


# ===================================================================
#
# SECTION 4: MAIN ALGORITHM LOOP (UPDATED TO PASS BLOCKED_SLOTS)
#
# ===================================================================

def run_genetic_algorithm(
    tasks_to_schedule: List[Task],
    blocked_slots: List[BlockedTimeSlot],
    population_size: int,
    generations: int,
    mutation_rate: float
) -> Schedule:
    """The main function that orchestrates the genetic algorithm."""
    population = [initialize_schedule(tasks_to_schedule, blocked_slots) for _ in range(population_size)]

    for gen in range(generations):
        # Evaluation
        for schedule in population:
            if schedule.fitness == -1.0:
                calculate_fitness(schedule, blocked_slots)
        
        # Elitism
        population.sort(key=lambda s: s.fitness, reverse=True)
        elitism_count = max(2, int(population_size * 0.1))
        next_generation = population[:elitism_count]
        
        # Reproduction
        selected_parents = selection(population)
        
        while len(next_generation) < population_size:
            p1, p2 = random.sample(selected_parents, 2)
            # Pass blocked_slots to crossover
            child = crossover(p1, p2, blocked_slots) 
            if random.random() < mutation_rate:
                # Pass blocked_slots to mutate
                child = mutate(child, blocked_slots)
            
            child.fitness = -1.0
            next_generation.append(child)
        
        population = next_generation
        
        if (gen + 1) % 10 == 0 or gen == 0:
            print(f"Thế hệ {gen + 1}/{generations} - Fitness tốt nhất: {population[0].fitness:.2f}")

    best_schedule = max(population, key=lambda s: s.fitness)
    return best_schedule