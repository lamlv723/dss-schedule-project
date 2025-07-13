import random
from .models import Schedule, Task, WORKING_DAYS, WORK_START_SLOT, WORK_END_SLOT
from collections import defaultdict # for calculate_fitness


def initialize_schedule(tasks_to_schedule: list[Task]) -> Schedule:
    """
    Tạo ra một Schedule ngẫu nhiên bằng cách xếp các công việc vào các vị trí trống.
    """
    new_schedule = Schedule(tasks_to_schedule)

    # Tạo danh sách tất cả các slot làm việc có thể xếp lịch
    available_slots = []
    for day_index, _ in enumerate(WORKING_DAYS):
        for slot_index in range(WORK_START_SLOT, WORK_END_SLOT):
            available_slots.append((day_index, slot_index))

    # Xáo trộn các vị trí một cách ngẫu nhiên
    random.shuffle(available_slots)

    # Xếp từng task vào các slot đã xáo trộn
    for task in new_schedule.tasks:
        is_placed = False
        while not is_placed and available_slots:
            # Lấy một vị trí ngẫu nhiên để thử đặt task
            start_day_idx, start_slot_idx = available_slots.pop(0)

            # Kiểm tra xem task có đủ chỗ để đặt không
            if start_slot_idx + task.duration <= WORK_END_SLOT:

                # Giả định vị trí này hợp lệ và đặt task vào
                # (Chúng ta sẽ xử lý xung đột sau trong hàm fitness)
                new_schedule.timetable[(start_day_idx, start_slot_idx)] = task
                is_placed = True

        if not is_placed:
            print(f"CẢNH BÁO: Không đủ chỗ cho công việc {task.name}")

    return new_schedule


def calculate_fitness(schedule: Schedule) -> float:
    """
    Tính toán và trả về điểm fitness cho một lịch trình.
    Điểm càng cao, lịch trình càng tốt.
    """
    score = 0

    # Tạo một cấu trúc để kiểm tra xung đột
    # Key: (day_idx, slot_idx), Value: số lượng task được gán vào slot đó
    slot_occupancy = defaultdict(int)

    # Lấy tất cả các slot đã được sử dụng
    all_used_slots = []

    for (start_day_idx, start_slot_idx), task in schedule.timetable.items():
        # 1. Thưởng điểm dựa trên độ ưu tiên
        score += task.priority * 10

        # Thưởng thêm nếu task được xếp trước 12h trưa (slot 24)
        if start_slot_idx < 24:
            score += 5 

        # Ghi nhận các slot mà task này chiếm dụng
        for i in range(task.duration):
            current_slot = (start_day_idx, start_slot_idx + i)
            slot_occupancy[current_slot] += 1
            all_used_slots.append(current_slot)

    # 2. Phạt nặng các xung đột (collision)
    collisions = 0
    for slot, count in slot_occupancy.items():
        if count > 1:
            # Mỗi task thừa trong một slot là một xung đột
            collisions += (count - 1)
    score -= collisions * 1000  # Phạt rất nặng

    # 3. Phạt các "lỗ hổng" thời gian
    if all_used_slots:
        # Sắp xếp các slot đã dùng để tìm lỗ hổng
        all_used_slots.sort()
        gaps = 0
        for i in range(len(all_used_slots) - 1):
            current_day, current_slot = all_used_slots[i]
            next_day, next_slot = all_used_slots[i+1]

            # Chỉ xét lỗ hổng trong cùng một ngày
            if current_day == next_day:
                gap_size = next_slot - (current_slot + 1)
                if gap_size > 0:
                    gaps += gap_size
        score -= gaps * 1 # Phạt nhẹ cho mỗi slot trống

    schedule.fitness = score
    return score


def selection(population: list[Schedule]) -> list[Schedule]:
    """
    Lựa chọn những cá thể tốt nhất từ quần thể để lai ghép.
    Sử dụng phương pháp "Tournament Selection".
    """
    selected = []
    for _ in range(len(population)):
        # Lấy ngẫu nhiên 2 cá thể từ quần thể để "so tài"
        participant1 = random.choice(population)
        participant2 = random.choice(population)
        # Chọn cá thể có điểm fitness cao hơn
        winner = participant1 if participant1.fitness > participant2.fitness else participant2
        selected.append(winner)
    return selected

def crossover(parent1: Schedule, parent2: Schedule) -> Schedule:
    """
    Lai ghép 2 cá thể cha mẹ để tạo ra một cá thể con.
    Phương pháp: Lấy một nửa số task của cha và một nửa của mẹ.
    """
    num_tasks_from_parent1 = len(parent1.tasks) // 2

    # Lấy task từ cha mẹ
    child_tasks = parent1.tasks[:num_tasks_from_parent1] + parent2.tasks[num_tasks_from_parent1:]

    # Tạo một lịch trình ngẫu nhiên mới từ bộ task đã lai ghép
    # Đây là cách đơn giản để đảm bảo lịch trình con hợp lệ
    child_schedule = initialize_schedule(child_tasks)
    return child_schedule

def mutate(schedule: Schedule) -> Schedule:
    """
    Gây đột biến nhẹ cho một lịch trình để tạo ra sự đa dạng.
    Phương pháp: Hoán đổi vị trí của 2 công việc ngẫu nhiên.
    """
    # Lấy 2 vị trí ngẫu nhiên trong timetable để hoán đổi
    keys = list(schedule.timetable.keys())
    if len(keys) > 1:
        key1, key2 = random.sample(keys, 2)

        # Hoán đổi task tại 2 vị trí này
        schedule.timetable[key1], schedule.timetable[key2] = schedule.timetable[key2], schedule.timetable[key1]

    return schedule


def run_genetic_algorithm(tasks_to_schedule: list[Task], population_size: int, generations: int):
    """
    Hàm chính để chạy toàn bộ thuật toán di truyền.
    """
    # 1. Khởi tạo quần thể ban đầu
    population = [initialize_schedule(tasks_to_schedule) for _ in range(population_size)]

    for gen in range(generations):
        # 2. Đánh giá quần thể
        for schedule in population:
            calculate_fitness(schedule)

        # 3. Lựa chọn các cá thể tốt nhất
        selected_parents = selection(population)

        # 4. Tạo thế hệ mới
        next_generation = []
        for i in range(0, len(selected_parents), 2):
            parent1 = selected_parents[i]
            # Đảm bảo có đủ cha mẹ để lai ghép
            parent2 = selected_parents[i+1] if (i+1) < len(selected_parents) else selected_parents[0]

            # 5. Lai ghép và Đột biến
            child = crossover(parent1, parent2)

            # Áp dụng đột biến với một xác suất nhỏ (ví dụ 10%)
            if random.random() < 0.1:
                child = mutate(child)

            next_generation.append(child)

        population = next_generation

        # In ra thông tin của thế hệ hiện tại để theo dõi
        best_fitness_in_gen = max(schedule.fitness for schedule in population)
        print(f"Thế hệ {gen + 1}/{generations} - Fitness tốt nhất: {best_fitness_in_gen:.2f}")

    # Trả về cá thể tốt nhất trong quần thể cuối cùng
    best_schedule = max(population, key=lambda s: s.fitness)
    return best_schedule