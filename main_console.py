from core.algorithm import initialize_schedule
from core.models import Task, WORKING_DAYS

if __name__ == "__main__":
    all_tasks = [
        Task(name="Làm đồ án DSS", duration=4, priority=3),
        Task(name="Học Tiếng Anh", duration=3, priority=2),
        Task(name="Tập thể dục", duration=2, priority=1),
        Task(name="Họp nhóm", duration=3, priority=3),
        Task(name="Đọc sách", duration=2, priority=1),
    ]

    print("--- Đang tạo một lịch trình ngẫu nhiên ---")
    random_schedule = initialize_schedule(tasks_to_schedule=all_tasks)

    print("\n--- KẾT QUẢ LỊCH TRÌNH NGẪU NHIÊN ---")
    if not random_schedule.timetable:
        print("Không có công việc nào được xếp.")
    else:
        # Sắp xếp và in ra cho dễ nhìn
        sorted_items = sorted(random_schedule.timetable.items())
        for (day_idx, slot_idx), task in sorted_items:
            day_name = WORKING_DAYS[day_idx]
            # Chuyển slot thành giờ:phút
            start_hour = slot_idx // 2
            start_minute = (slot_idx % 2) * 30
            print(f"[{day_name}] {start_hour:02d}:{start_minute:02d} -> {task.name}")