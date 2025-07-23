# ga_core/fitness.py

import math
from datetime import datetime, timedelta
from config import app_config, ga_config

def calculate_fitness(individual, tasks_map, blocked_slots):
    """
    Calculates the fitness of a schedule (individual).
    HIGHER scores are better. The function returns a tuple required by DEAP.
    """
    
    # --- Hard Constraint Validation ---
    # In a maximization problem, an invalid schedule should have the lowest fitness: 0.0
    
    scheduled_slots = {}
    task_finish_times = {}
    
    individual.sort(key=lambda x: x[1])

    for task_id, start_slot in individual:
        task = tasks_map.get(task_id)
        if not task:
            return (0.0,) # <<< FIX: Invalid task ID returns 0.0

        duration = task.get('estimated_time', 1)
        end_slot = start_slot + duration

        for slot in range(start_slot, end_slot):
            if slot in scheduled_slots or slot in blocked_slots:
                return (0.0,) # <<< FIX: Overlap or blocked time returns 0.0
            scheduled_slots[slot] = task_id
        
        task_finish_times[task_id] = end_slot

    for task_id, start_slot in individual:
        task = tasks_map.get(task_id)
        if task.get('predecessor_task_id'):
            pred_id = task['predecessor_task_id']
            pred_instance_id = next((tid for tid, t in tasks_map.items() if t.get('original_id') == pred_id), None)

            if pred_instance_id in task_finish_times:
                pred_finish_time = task_finish_times[pred_instance_id]
                if start_slot < pred_finish_time:
                    return (0.0,) # <<< FIX: Precedence violation returns 0.0

    for task_id, start_slot in individual:
        task = tasks_map.get(task_id)
        if task.get('earliest_start_time'):
            try:
                earliest_start_dt = datetime.fromisoformat(task['earliest_start_time'])
                schedule_start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                earliest_start_slot = (earliest_start_dt - schedule_start_dt).total_seconds() / (app_config.TIME_SLOT_DURATION * 60)
                if start_slot < earliest_start_slot:
                    return (0.0,) # <<< FIX: Earliest start violation returns 0.0
            except (ValueError, TypeError):
                pass

    # --- Soft Constraint Penalty Calculation ---
    total_penalty = 0.0
    
    # Priority Penalty
    priority_penalty = sum((1 / tasks_map[tid]['priority']) * start for tid, start in individual if tasks_map.get(tid) and tasks_map[tid].get('priority', 0) > 0)
    total_penalty += ga_config.FITNESS_WEIGHTS['priority'] * priority_penalty

    # Deadline Penalty
    deadline_penalty = 0
    schedule_start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for task_id, start_slot in individual:
        task = tasks_map.get(task_id)
        if not task: continue
        if task.get('deadline'):
            try:
                deadline_dt = datetime.fromisoformat(task['deadline'])
                finish_slot = start_slot + task['estimated_time']
                finish_dt = schedule_start_dt + timedelta(minutes=finish_slot * app_config.TIME_SLOT_DURATION)
                if finish_dt > deadline_dt:
                    lateness = (finish_dt - deadline_dt).total_seconds() / 3600
                    deadline_penalty += lateness ** 2
            except (ValueError, TypeError):
                pass
    total_penalty += ga_config.FITNESS_WEIGHTS['deadline'] * deadline_penalty

    # Idle Time Penalty
    idle_time_penalty = 0
    slots_by_day = [[] for _ in range(app_config.DAYS_IN_SCHEDULE)]
    for slot in scheduled_slots.keys():
        day = slot // app_config.SLOTS_PER_DAY
        if day < len(slots_by_day):
            slots_by_day[day].append(slot)
    
    for day_slots in slots_by_day:
        if len(day_slots) > 1:
            min_slot = min(day_slots)
            max_slot = max(day_slots)
            day_span = max_slot - min_slot
            active_time = len(day_slots)
            idle_time_penalty += (day_span - active_time)
    total_penalty += ga_config.FITNESS_WEIGHTS['idle_time'] * idle_time_penalty

    # Category Switching Penalty
    category_penalty = 0
    for i in range(len(individual) - 1):
        task1_id = individual[i][0]
        task2_id = individual[i+1][0]
        
        task1 = tasks_map.get(task1_id)
        task2 = tasks_map.get(task2_id)
        
        if task1 and task2:
            cat1 = task1.get('category')
            cat2 = task2.get('category')
            if cat1 and cat2 and cat1 != cat2:
                category_penalty += 1
    total_penalty += ga_config.FITNESS_WEIGHTS['category_switching'] * category_penalty

    # Convert the total penalty into a fitness score (higher is better)
    fitness_score = ga_config.MAX_FITNESS_SCORE / (1.0 + total_penalty)

    return (fitness_score,)