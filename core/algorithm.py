import random
from collections import defaultdict
from .models import *

# --- 1. HÀM KHỞI TẠO ĐÃ ĐƯỢC CẢI TIẾN ---
def initialize_schedule(tasks_to_schedule: list[Task]) -> Schedule:
    """
    Tạo Schedule ngẫu nhiên, ưu tiên task quan trọng và xếp càng sớm càng tốt.
    """
    new_schedule = Schedule(tasks_to_schedule)
    occupied_slots = set()

    # Sắp xếp task theo độ ưu tiên tăng dần (1 là ưu tiên cao nhất)
    sorted_tasks = sorted(tasks_to_schedule, key=lambda x: x.priority, reverse=False)

    # --- Hàm phụ để xếp lịch ---
    def _place_tasks(tasks, available_slots):
        # KHÔNG XÁO TRỘN SLOT NỮA để ưu tiên xếp sớm
        # random.shuffle(available_slots)
        for task in tasks:
            # Tìm một vị trí ngẫu nhiên trong danh sách slot để bắt đầu tìm kiếm
            # Điều này giúp tạo ra sự đa dạng ban đầu
            start_search_index = random.randint(0, len(available_slots) - 1)
            
            # Duyệt vòng tròn để đảm bảo thử hết các slot
            for i in range(len(available_slots)):
                slot_index = (start_search_index + i) % len(available_slots)
                start_day_idx, start_slot_idx = available_slots[slot_index]

                day_end_slot = WORK_END_SLOT if task.is_work_time else SLOTS_PER_DAY
                if start_slot_idx + task.duration > day_end_slot:
                    continue

                needed_slots = [(start_day_idx, start_slot_idx + j) for j in range(task.duration)]
                if not any(slot in occupied_slots for slot in needed_slots):
                    new_schedule.timetable[(start_day_idx, start_slot_idx)] = task
                    occupied_slots.update(needed_slots)
                    break
    
    work_tasks = [t for t in sorted_tasks if t.is_work_time]
    off_hours_tasks = [t for t in sorted_tasks if not t.is_work_time]

    # Tạo danh sách slot và xếp lịch
    work_time_slots = [(d, s) for d in range(len(WORKING_DAYS)) for s in range(WORK_START_SLOT, WORK_END_SLOT)]
    off_hours_slots = [(d, s) for d in range(len(WORKING_DAYS)) for s in list(range(0, WORK_START_SLOT)) + list(range(WORK_END_SLOT, SLOTS_PER_DAY))]
    
    _place_tasks(work_tasks, work_time_slots)
    _place_tasks(off_hours_tasks, off_hours_slots)

    return new_schedule

# --- 2. HÀM FITNESS ĐÃ ĐƯỢC CẢI TIẾN ---
def calculate_fitness(schedule: Schedule) -> float:
    """
    Tính điểm fitness. Thưởng cho việc xếp sớm và ưu tiên cao.
    """
    score = 0
    all_used_slots = []

    for (day_idx, start_slot_idx), task in schedule.timetable.items():
        # Thưởng điểm dựa trên độ ưu tiên (priority 1 được thưởng nhiều nhất)
        score += (TOTAL_PRIORITY_LEVELS - task.priority) * 10
        
        # Thưởng CÀNG NHIỀU nếu xếp CÀNG SỚM
        # (5 ngày * 48 slot/ngày) = 240. Ta lấy max trừ đi để slot càng nhỏ điểm càng cao.
        earliness_bonus = (len(WORKING_DAYS) * SLOTS_PER_DAY) - (day_idx * SLOTS_PER_DAY + start_slot_idx)
        score += earliness_bonus * 0.1 # Trọng số nhỏ để không lấn át priority

        for i in range(task.duration):
            all_used_slots.append((day_idx, start_slot_idx + i))

    # Phạt các "lỗ hổng" thời gian
    if all_used_slots:
        all_used_slots.sort()
        gaps = 0
        for i in range(len(all_used_slots) - 1):
            current_day, current_slot = all_used_slots[i]
            next_day, next_slot = all_used_slots[i+1]
            if current_day == next_day:
                gap_size = next_slot - (current_slot + 1)
                if gap_size > 0:
                    gaps += gap_size
        score -= gaps * 1
        
    schedule.fitness = score
    return score

# --- 3. HÀM CROSSOVER VÀ MUTATE ĐÃ ĐƯỢC CẢI TIẾN ---
def selection(population: list[Schedule]) -> list[Schedule]:
    """Tournament Selection"""
    selected = []
    pop_size = len(population)
    for _ in range(pop_size):
        # Lấy ra 5% của quần thể để "so tài", tối thiểu 2
        tournament_size = max(2, int(pop_size * 0.05))
        participants = random.sample(population, tournament_size)
        winner = max(participants, key=lambda s: s.fitness)
        selected.append(winner)
    return selected

def crossover(parent1: Schedule, parent2: Schedule) -> Schedule:
    """
    Lai ghép thực sự: Kết hợp timetable của cha mẹ và sửa lỗi xung đột.
    """
    child_tasks = parent1.tasks
    child_schedule = Schedule(child_tasks)
    
    # Lấy một nửa task từ parent1
    for i, ((day, slot), task) in enumerate(parent1.timetable.items()):
        if i % 2 == 0:
             child_schedule.timetable[(day, slot)] = task

    # Lấy nửa còn lại từ parent2, sửa xung đột nếu có
    occupied_slots = {(d, s + i) for (d, s), t in child_schedule.timetable.items() for i in range(t.duration)}
    
    for (day, slot), task in parent2.timetable.items():
        # Nếu task này chưa có trong lịch trình của con
        if task not in child_schedule.timetable.values():
            needed_slots = {(day, slot + i) for i in range(task.duration)}
            # Nếu vị trí của cha mẹ 2 không bị xung đột
            if not needed_slots.intersection(occupied_slots):
                child_schedule.timetable[(day, slot)] = task
                occupied_slots.update(needed_slots)

    # Đảm bảo tất cả task đều được xếp lịch
    scheduled_tasks = set(child_schedule.timetable.values())
    missing_tasks = [t for t in child_tasks if t not in scheduled_tasks]
    if missing_tasks:
        # Nếu có task bị thiếu, ta khởi tạo lại ngẫu nhiên để đảm bảo tính toàn vẹn
        return initialize_schedule(child_tasks)

    return child_schedule

def mutate(schedule: Schedule) -> Schedule:
    """
    Đột biến: Tìm một task và chuyển nó đến một vị trí trống khác.
    """
    if not schedule.timetable:
        return schedule
        
    # Lấy ngẫu nhiên một task để di chuyển
    key_to_move = random.choice(list(schedule.timetable.keys()))
    task_to_move = schedule.timetable.pop(key_to_move)

    # Tìm một vị trí mới
    # (Đây là phiên bản đơn giản, có thể cải tiến thêm)
    temp_schedule = initialize_schedule(schedule.tasks)
    return temp_schedule


def run_genetic_algorithm(tasks_to_schedule: list[Task], population_size: int, generations: int):
    """
    Hàm chính để chạy thuật toán di truyền.
    """
    population = [initialize_schedule(tasks_to_schedule) for _ in range(population_size)]

    for gen in range(generations):
        # Đánh giá
        for schedule in population:
            calculate_fitness(schedule)
        
        # Sắp xếp và giữ lại những cá thể tốt nhất (Elitism)
        population.sort(key=lambda s: s.fitness, reverse=True)
        elitism_count = max(2, int(population_size * 0.1)) # Giữ lại 10% tốt nhất
        next_generation = population[:elitism_count]
        
        # Tạo ra phần còn lại của thế hệ mới
        selected_parents = selection(population)
        
        while len(next_generation) < population_size:
            parent1, parent2 = random.sample(selected_parents, 2)
            child = crossover(parent1, parent2)
            if random.random() < 0.2: # Tăng xác suất đột biến
                child = mutate(child)
            next_generation.append(child)
        
        population = next_generation
        
        best_fitness_in_gen = population[0].fitness
        print(f"Thế hệ {gen + 1}/{generations} - Fitness tốt nhất: {best_fitness_in_gen:.2f}")

    # Trả về cá thể tốt nhất cuối cùng
    best_schedule = max(population, key=lambda s: s.fitness)
    calculate_fitness(best_schedule) # Tính lại fitness lần cuối cho chắc chắn
    return best_schedule