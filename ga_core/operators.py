# ga_core/operators.py

import random
from config import app_config, ga_config
from deap import tools

def create_random_schedule(individual_class, task_instances, blocked_slots):
    """Creates a single random, but valid, schedule (an individual)."""
    schedule = []
    available_slots = list(set(range(app_config.TOTAL_TIME_SLOTS)) - set(blocked_slots))
    random.shuffle(task_instances)
    
    scheduled_slots = set()

    for task in task_instances:
        placed = False
        random.shuffle(available_slots)
        duration = task.get('estimated_time', 1)

        for start_slot in available_slots:
            end_slot = start_slot + duration
            
            # Check if the entire duration is free
            is_valid = True
            for slot in range(start_slot, end_slot):
                if slot in scheduled_slots or slot in blocked_slots:
                    is_valid = False
                    break
            
            if is_valid:
                schedule.append((task['instance_id'], start_slot))
                for slot in range(start_slot, end_slot):
                    scheduled_slots.add(slot)
                placed = True
                break
        
        # <<< FIX: Logic dự phòng thông minh hơn, kiểm tra toàn bộ thời lượng
        if not placed:
            # Fallback: if no non-overlapping slot is found, try to find the first possible valid slot
            for start_slot in range(app_config.TOTAL_TIME_SLOTS):
                end_slot = start_slot + duration
                is_valid = True
                # Check if this fallback slot is valid for the whole duration
                for slot in range(start_slot, end_slot):
                    if slot in scheduled_slots or slot in blocked_slots or slot >= app_config.TOTAL_TIME_SLOTS:
                        is_valid = False
                        break
                
                if is_valid:
                    schedule.append((task['instance_id'], start_slot))
                    for slot in range(start_slot, end_slot):
                        scheduled_slots.add(slot)
                    placed = True
                    break
            
            # If still not placed (highly constrained), it will be handled by the fitness function
            if not placed:
                # Add it at the beginning, it will receive a very low fitness score and be eliminated.
                schedule.append((task['instance_id'], 0))


    return individual_class(schedule)

def custom_crossover(ind1, ind2, task_instances):
    """Custom time-slot based crossover operator with repair."""
    cut_point = random.randint(0, app_config.TOTAL_TIME_SLOTS)
    
    child1_tasks = {task_id: start for task_id, start in ind1 if start < cut_point}
    
    # Add tasks from parent 2, avoiding duplicates
    for task_id, start in ind2:
        if start >= cut_point and task_id not in child1_tasks:
            child1_tasks[task_id] = start
            
    # <<< FIX: Corrected variable name from child_tasks to child1_tasks
    repaired_child_list = repair_schedule(child1_tasks, task_instances)
    
    # For simplicity, we create one child and modify ind1. ind2 is left unchanged.
    ind1[:] = repaired_child_list
    # A more complex implementation could create two distinct children.
    return ind1, ind2

def repair_schedule(child_tasks, all_task_instances):
    """Repairs an individual to ensure all tasks are present exactly once."""
    final_schedule = [] # <<< FIX: Initialized as an empty list
    all_instance_ids = {t['instance_id'] for t in all_task_instances}
    scheduled_ids = set(child_tasks.keys())

    # Add tasks that are correctly present
    for task_id in scheduled_ids.intersection(all_instance_ids):
        final_schedule.append((task_id, child_tasks[task_id]))

    # Identify missing tasks
    missing_ids = all_instance_ids - scheduled_ids
    
    if missing_ids:
        # Find available slots to place missing tasks
        occupied_slots = set()
        for _, start in final_schedule:
            # Need to consider task duration for occupied slots
            task_instance = next((t for t in all_task_instances if t['instance_id'] == _), None)
            if task_instance:
                duration = task_instance.get('estimated_time', 1)
                for i in range(duration):
                    occupied_slots.add(start + i)
            
        available_slots = list(set(range(app_config.TOTAL_TIME_SLOTS)) - occupied_slots)
        random.shuffle(available_slots)

        for task_id in missing_ids:
            if available_slots:
                start_slot = available_slots.pop(0) # Use pop(0) for some predictability
                final_schedule.append((task_id, start_slot))
            else:
                # Fallback: place at a random slot (will likely get high penalty)
                final_schedule.append((task_id, random.randint(0, app_config.TOTAL_TIME_SLOTS - 1)))

    return final_schedule


def custom_mutation(individual, blocked_slots):
    """Applies one of several intelligent mutation operators to a schedule."""
    if not individual:
        return individual,

    # Choose a mutation type based on predefined probabilities
    mutation_type = random.choices(
        list(ga_config.MUTATION_TYPE_PROBS.keys()),
        weights=list(ga_config.MUTATION_TYPE_PROBS.values()),
        k=1
    )[0] # random.choices returns a list

    if mutation_type == "reschedule":
        # Pick a random task and move it to a new valid time slot
        if len(individual) > 0:
            task_index = random.randint(0, len(individual) - 1)
            task_id, _ = individual[task_index]
            
            available_slots = list(set(range(app_config.TOTAL_TIME_SLOTS)) - set(blocked_slots))
            if available_slots:
                new_start_slot = random.choice(available_slots)
                individual[task_index] = (task_id, new_start_slot)

    elif mutation_type == "swap":
        # Swap the start times of two random tasks
        if len(individual) >= 2:
            idx1, idx2 = random.sample(range(len(individual)), 2)
            task1_id, start1 = individual[idx1]
            task2_id, start2 = individual[idx2]
            individual[idx1] = (task1_id, start2)
            individual[idx2] = (task2_id, start1)

    elif mutation_type == "creep":
        # Slightly shift a random task's start time
        if len(individual) > 0:
            task_index = random.randint(0, len(individual) - 1)
            task_id, start_slot = individual[task_index]
            
            shift = random.randint(-5, 5) # Creep range
            new_start_slot = max(0, min(app_config.TOTAL_TIME_SLOTS - 1, start_slot + shift))
            
            if new_start_slot not in blocked_slots:
                individual[task_index] = (task_id, new_start_slot)

    return individual,