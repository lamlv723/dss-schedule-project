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