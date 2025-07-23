# core/algorithm.py

import random
from typing import List, Optional, Tuple, Set, Dict

from .models import Task, Schedule, ScheduledTask
from . import configs
from . import utils

# --- Các hàm khác như calculate_fitness, create_individual, etc. giữ nguyên ---

def calculate_fitness(schedule: Schedule) -> float:
    fitness = 0
    if not schedule or not schedule.scheduled_tasks:
        return 0
    fitness += len(schedule.scheduled_tasks) * 100
    for scheduled_task in schedule.scheduled_tasks:
        fitness += scheduled_task.task.priority * 10
    return fitness

def create_individual(tasks: List[Task]) -> Schedule:
    schedule = Schedule(scheduled_tasks=[])
    schedule_matrix: List[List[Optional[Task]]] = [
        [None for _ in range(configs.SLOTS_PER_DAY)]
        for _ in range(configs.DAYS_IN_SCHEDULE)
    ]
    parent_task_day_map: dict[str, Set[int]] = {}
    for task in tasks:
        task_slots = utils.task_duration_to_slots(task.duration)
        for _ in range(100):
            day = random.randint(0, configs.DAYS_IN_SCHEDULE - 1)
            if task.parent_task and task.parent_task in parent_task_day_map and day in parent_task_day_map[task.parent_task]:
                continue
            start_slot = random.randint(0, configs.SLOTS_PER_DAY - task_slots)
            is_valid_spot = True
            for i in range(task_slots):
                slot_to_check = start_slot + i
                if schedule_matrix[day][slot_to_check] is not None or \
                   utils.is_time_blocked(day, slot_to_check, configs.BLOCKED_TIME_SLOTS):
                    is_valid_spot = False
                    break
            if is_valid_spot:
                scheduled_task = ScheduledTask(task=task, day=day, start_time=start_slot)
                schedule.scheduled_tasks.append(scheduled_task)
                for i in range(task_slots):
                    schedule_matrix[day][start_slot + i] = task
                if task.parent_task:
                    if task.parent_task not in parent_task_day_map:
                        parent_task_day_map[task.parent_task] = set()
                    parent_task_day_map[task.parent_task].add(day)
                break
    return schedule

def initialize_population(tasks: List[Task]) -> List[Schedule]:
    return [create_individual(tasks) for _ in range(configs.POPULATION_SIZE)]

def select_parents(population: List[Schedule], fitness_scores: List[float]) -> Tuple[Schedule, Schedule]:
    tournament_size = 5
    def tournament() -> Schedule:
        contenders_indices = random.sample(range(len(population)), tournament_size)
        best_contender_index = max(contenders_indices, key=lambda i: fitness_scores[i])
        return population[best_contender_index]
    return tournament(), tournament()

def crossover(parent1: Schedule, parent2: Schedule, demo_log: List[str]):
    """
    Chooses the better parent and appends the demonstration steps to the demo_log list.
    """
    fitness1 = calculate_fitness(parent1)
    fitness2 = calculate_fitness(parent2)

    demo_log.append("--- [DEMO] Bắt đầu quá trình Lai tạo (Elitism) ---")
    demo_log.append(f"1.  **Chọn Bố Mẹ**:")
    demo_log.append(f"    - Bố 1 có điểm Fitness: {fitness1:.2f} ({len(parent1.scheduled_tasks)} công việc)")
    demo_log.append(f"    - Bố 2 có điểm Fitness: {fitness2:.2f} ({len(parent2.scheduled_tasks)} công việc)")
    demo_log.append("2.  **So sánh và Lựa chọn**:")

    if fitness1 > fitness2:
        demo_log.append("    - -> Chọn Bố 1 vì có điểm Fitness cao hơn.")
        demo_log.append("--- [DEMO] Kết thúc ---")
        return parent1
    else:
        demo_log.append("    - -> Chọn Bố 2 vì có điểm Fitness cao hơn (hoặc bằng).")
        demo_log.append("--- [DEMO] Kết thúc ---")
        return parent2

def mutate(schedule: Schedule, tasks: List[Task], demo_log: List[str]) -> Schedule:
    """
    Applies mutation and logs the action if it happens.
    """
    if random.random() < configs.MUTATION_RATE:
        demo_log.append("--- [DEMO] Thực hiện Đột biến! Tạo ra một cá thể hoàn toàn mới. ---")
        return create_individual(tasks)
    return schedule

def run_genetic_algorithm(tasks: List[Task]) -> Tuple[Schedule, List[str]]:
    """
    The main algorithm function. Now returns both the best schedule and a log of demo messages.
    """
    demo_log: List[str] = []
    expanded_tasks = utils.expand_tasks_by_frequency(tasks)
    population = initialize_population(expanded_tasks)
    
    best_schedule = population[0]
    best_fitness = calculate_fitness(best_schedule)

    for generation in range(configs.NUM_GENERATIONS):
        fitness_scores = [calculate_fitness(ind) for ind in population]
        for i, score in enumerate(fitness_scores):
            if score > best_fitness:
                best_fitness = score
                best_schedule = population[i]

        new_population = [best_schedule]

        while len(new_population) < configs.POPULATION_SIZE:
            parent1, parent2 = select_parents(population, fitness_scores)
            
            # Crossover and mutate will now add messages to the demo_log list
            child = crossover(parent1, parent2, demo_log)
            mutated_child = mutate(child, expanded_tasks, demo_log)
            
            new_population.append(mutated_child)
            
        population = new_population

    return best_schedule, demo_log