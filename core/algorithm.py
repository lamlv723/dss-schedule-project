import random
from typing import List
from copy import deepcopy

# Import utilities, models, and configs
from .utils import find_valid_spot_for_task, calculate_adaptive_rate
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
# SECTION 2: FITNESS CALCULATION
#
# ===================================================================

def calculate_fitness(schedule: Schedule, blocked_slots: List[BlockedTimeSlot]) -> float:
    """Calculates the fitness score of a given schedule."""
    if not schedule.scheduled_tasks: return 0.0
    score = 1000.0
    sorted_tasks = sorted(schedule.scheduled_tasks, key=lambda x: (configs.DAYS_OF_WEEK.index(x.day), x.start_slot))
    days_in_schedule = {st.day for st in sorted_tasks}
    
    total_slots_in_week = len(configs.DAYS_OF_WEEK) * configs.SLOTS_PER_DAY
    for st in sorted_tasks:
        priority_weight = (configs.TOTAL_PRIORITY_LEVELS - st.task.priority) ** 2
        time_position_score = total_slots_in_week - (configs.DAYS_OF_WEEK.index(st.day) * configs.SLOTS_PER_DAY + st.start_slot)
        score += priority_weight * time_position_score * 0.5

    for i in range(len(sorted_tasks) - 1):
        current_task, next_task = sorted_tasks[i], sorted_tasks[i+1]
        if current_task.day == next_task.day:
            gap = next_task.start_slot - (current_task.start_slot + current_task.task.duration)
            if gap > 1: score -= gap * 5

    if days_in_schedule:
        score -= (len(days_in_schedule) - 1) * 100
        
    if len(days_in_schedule) > 1:
        first_day_index = configs.DAYS_OF_WEEK.index(sorted_tasks[0].day)
        last_day_index = configs.DAYS_OF_WEEK.index(sorted_tasks[-1].day)
        for day_index in range(first_day_index + 1, last_day_index):
            day_name = configs.DAYS_OF_WEEK[day_index]
            if day_name not in days_in_schedule:
                score -= 75

    schedule.fitness = score
    return score

# ===================================================================
#
# SECTION 3: GENETIC OPERATORS
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
    """Creates a new, valid child schedule by combining two parents with a repair mechanism."""
    child = Schedule()
    tasks_from_p1 = [st for st in parent1.scheduled_tasks if random.random() < 0.5]
    child.scheduled_tasks = deepcopy(tasks_from_p1)
    
    scheduled_task_names = {st.task.name for st in child.scheduled_tasks}
    tasks_to_schedule = [st.task for st in parent2.scheduled_tasks if st.task.name not in scheduled_task_names]
    random.shuffle(tasks_to_schedule)

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
    """Applies a random, valid change to a schedule by moving a single task."""
    if len(schedule.scheduled_tasks) < 2: return schedule
    mutated_schedule = deepcopy(schedule)
    task_to_move = mutated_schedule.scheduled_tasks.pop(random.randrange(len(mutated_schedule.scheduled_tasks)))

    occupied_slots = {day: [False] * configs.SLOTS_PER_DAY for day in configs.DAYS_OF_WEEK}
    for st in mutated_schedule.scheduled_tasks:
        for i in range(st.task.duration):
            occupied_slots[st.day][st.start_slot + i] = True

    spot = find_valid_spot_for_task(task_to_move.task, occupied_slots, blocked_slots)

    if spot:
        day, start_slot = spot
        mutated_schedule.scheduled_tasks.append(ScheduledTask(task=task_to_move.task, day=day, start_slot=start_slot))
        return mutated_schedule
    else:
        return schedule

# ===================================================================
#
# SECTION 4: MAIN ALGORITHM LOOP (NOW WITH ADAPTIVE RATES)
#
# ===================================================================

def run_genetic_algorithm(
    tasks_to_schedule: List[Task],
    blocked_slots: List[BlockedTimeSlot],
    population_size: int,
    generations: int
) -> Schedule:
    """The main function that orchestrates the adaptive genetic algorithm."""
    population = [initialize_schedule(tasks_to_schedule, blocked_slots) for _ in range(population_size)]

    for gen in range(generations):
        # --- Evaluation ---
        for schedule in population:
            if schedule.fitness == -1.0:
                calculate_fitness(schedule, blocked_slots)
        
        population.sort(key=lambda s: s.fitness, reverse=True)

        # --- Adaptive Rate Calculation ---
        fitness_values = [s.fitness for s in population if s.fitness != -1.0]
        if not fitness_values: break # Stop if population is invalid
        
        max_fitness = fitness_values[0]
        avg_fitness = sum(fitness_values) / len(fitness_values)

        # --- Elitism ---
        elitism_count = max(2, int(population_size * 0.1))
        next_generation = population[:elitism_count]
        
        # --- Reproduction with Adaptive Rates ---
        selected_parents = selection(population)
        
        while len(next_generation) < population_size:
            p1, p2 = random.sample(selected_parents, 2)
            
            # Calculate adaptive crossover rate for this specific pair
            crossover_rate = calculate_adaptive_rate(
                max(p1.fitness, p2.fitness), max_fitness, avg_fitness, configs.ADAPTIVE_K_CROSSOVER
            )

            if random.random() < crossover_rate:
                child = crossover(p1, p2, blocked_slots)
            else:
                child = deepcopy(p1) # If no crossover, child is a clone of the first parent
            
            # Calculate adaptive mutation rate for the new child
            mutation_rate = calculate_adaptive_rate(
                child.fitness, max_fitness, avg_fitness, configs.ADAPTIVE_K_MUTATION
            )

            if random.random() < mutation_rate:
                child = mutate(child, blocked_slots)
            
            child.fitness = -1.0
            next_generation.append(child)
        
        population = next_generation
        
        if (gen + 1) % 10 == 0 or gen == 0 or gen == generations - 1:
            print(f"Thế hệ {gen + 1}/{generations} - Fitness tốt nhất: {population[0].fitness:.2f}")

    best_schedule = max(population, key=lambda s: s.fitness)
    return best_schedule