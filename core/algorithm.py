import random
from typing import List, Optional, Tuple, Set

from .models import Task, Schedule, ScheduledTask
from . import configs
from . import utils

# Type alias for a schedule representation
Chromosome = List[Optional[ScheduledTask]]

def calculate_fitness(schedule: Schedule) -> float:
    """
    Calculates the fitness score of a schedule.
    A higher score indicates a better schedule.
    
    The fitness function can be complex, considering factors like:
    - Number of tasks scheduled (more is better).
    - Priority of scheduled tasks (higher priority is better).
    - Gaps between tasks (fewer gaps might be better).
    - Tasks scheduled during preferred times.
    """
    fitness = 0
    if not schedule or not schedule.scheduled_tasks:
        return 0

    # Higher score for scheduling more tasks
    fitness += len(schedule.scheduled_tasks) * 100

    # Add points based on the priority of each scheduled task
    for scheduled_task in schedule.scheduled_tasks:
        fitness += scheduled_task.task.priority * 10
    
    return fitness

def create_individual(tasks: List[Task]) -> Schedule:
    """
    Creates a single random, valid schedule (an "individual" in the population).
    This function now respects the frequency constraint.
    """
    schedule = Schedule(scheduled_tasks=[])
    
    # A 2D matrix to represent the schedule grid for easy collision checks
    # Dimensions are (days, slots_per_day)
    schedule_matrix: List[List[Optional[Task]]] = [
        [None for _ in range(configs.SLOTS_PER_DAY)]
        for _ in range(configs.DAYS_IN_SCHEDULE)
    ]

    # A dictionary to track which day a parent task has been placed on
    # Key: parent_task_name (str), Value: set of days (int)
    parent_task_day_map: dict[str, Set[int]] = {}

    for task in tasks:
        task_slots = utils.task_duration_to_slots(task.duration)
        placed = False
        
        # Try to place the task a certain number of times
        for _ in range(100):
            day = random.randint(0, configs.DAYS_IN_SCHEDULE - 1)
            
            # --- New Constraint Check ---
            # If this is a child task, check if its parent is already on this day.
            if task.parent_task:
                # If the parent is in the map and this day is already used, skip
                if task.parent_task in parent_task_day_map and day in parent_task_day_map[task.parent_task]:
                    continue # Try another day
            
            start_slot = random.randint(0, configs.SLOTS_PER_DAY - task_slots)
            
            # Check if the chosen spot is valid
            is_valid_spot = True
            for i in range(task_slots):
                slot_to_check = start_slot + i
                if schedule_matrix[day][slot_to_check] is not None or \
                   utils.is_time_blocked(day, slot_to_check, configs.BLOCKED_TIME_SLOTS):
                    is_valid_spot = False
                    break
            
            if is_valid_spot:
                # Place the task
                scheduled_task = ScheduledTask(task=task, day=day, start_time=start_slot)
                schedule.scheduled_tasks.append(scheduled_task)
                
                for i in range(task_slots):
                    schedule_matrix[day][start_slot + i] = task
                
                # --- Update Parent Task Map ---
                if task.parent_task:
                    if task.parent_task not in parent_task_day_map:
                        parent_task_day_map[task.parent_task] = set()
                    parent_task_day_map[task.parent_task].add(day)
                
                placed = True
                break
        
        # If the task could not be placed, it is left unscheduled for this individual
    
    return schedule

def initialize_population(tasks: List[Task]) -> List[Schedule]:
    """Creates the initial population of random schedules."""
    return [create_individual(tasks) for _ in range(configs.POPULATION_SIZE)]

def select_parents(population: List[Schedule], fitness_scores: List[float]) -> Tuple[Schedule, Schedule]:
    """
    Selects two parent schedules from the population using tournament selection.
    """
    # Simple tournament selection
    tournament_size = 5
    
    def tournament() -> Schedule:
        contenders_indices = random.sample(range(len(population)), tournament_size)
        best_contender_index = max(contenders_indices, key=lambda i: fitness_scores[i])
        return population[best_contender_index]

    parent1 = tournament()
    parent2 = tournament()
    
    return parent1, parent2

def crossover(parent1: Schedule, parent2: Schedule) -> Schedule:
    """
    Creates a new child schedule by combining two parent schedules.
    This function is simplified and does not yet respect the frequency constraint.
    For a robust solution, crossover needs to be more intelligent, potentially
    re-validating the child schedule. For now, we return the better parent.
    """
    # A simple crossover: return the parent with the higher fitness.
    # A more advanced crossover would combine parts of both parents and then
    # run a repair function to fix constraint violations.
    fitness1 = calculate_fitness(parent1)
    fitness2 = calculate_fitness(parent2)

    return parent1 if fitness1 > fitness2 else parent2

def mutate(schedule: Schedule, tasks: List[Task]) -> Schedule:
    """
    Applies a mutation to a schedule by randomly moving or swapping tasks.
    This function is simplified. A robust implementation needs to ensure
    the mutation results in a valid schedule according to all constraints.
    """
    # For now, mutation is a simple re-creation of an individual.
    # This is not efficient but ensures validity.
    if random.random() < configs.MUTATION_RATE:
        return create_individual(tasks)
    return schedule


def run_genetic_algorithm(tasks: List[Task]) -> Schedule:
    """
    The main function that orchestrates the genetic algorithm process.
    """
    # 1. Expand tasks by their frequency
    expanded_tasks = utils.expand_tasks_by_frequency(tasks)
    
    # 2. Initialize population
    population = initialize_population(expanded_tasks)
    
    best_schedule = None
    best_fitness = -1

    for generation in range(configs.NUM_GENERATIONS):
        # 3. Calculate fitness for each individual
        fitness_scores = [calculate_fitness(ind) for ind in population]

        # Find the best schedule in the current generation
        for i, score in enumerate(fitness_scores):
            if score > best_fitness:
                best_fitness = score
                best_schedule = population[i]

        # 4. Create the next generation
        new_population = [best_schedule] # Elitism: carry over the best individual

        while len(new_population) < configs.POPULATION_SIZE:
            # 5. Select parents
            parent1, parent2 = select_parents(population, fitness_scores)
            
            # 6. Crossover
            child = crossover(parent1, parent2)
            
            # 7. Mutate
            mutated_child = mutate(child, expanded_tasks)
            
            new_population.append(mutated_child)
            
        population = new_population
        
        # Optional: print progress
        # print(f"Generation {generation + 1}: Best Fitness = {best_fitness}")

    return best_schedule