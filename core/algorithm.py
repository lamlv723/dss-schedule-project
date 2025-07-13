import random
from .models import Schedule, Task, WORKING_DAYS, WORK_START_SLOT, WORK_END_SLOT

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