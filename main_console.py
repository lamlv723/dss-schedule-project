from core.models import Task, WORKING_DAYS
from core.algorithm import initialize_schedule, calculate_fitness

if __name__ == "__main__":
    all_tasks = [
        Task(name="Làm đồ án DSS", duration=4, priority=3),      # 2 tiếng
        Task(name="Học Tiếng Anh", duration=3, priority=2),   # 1.5 tiếng
        Task(name="Tập thể dục", duration=2, priority=1),     # 1 tiếng
        Task(name="Họp nhóm", duration=3, priority=3),         # 1.5 tiếng
        Task(name="Đọc sách", duration=2, priority=1),         # 1 tiếng
    ]

    print("--- Đang tạo một lịch trình ngẫu nhiên ---")
    random_schedule = initialize_schedule(tasks_to_schedule=all_tasks)

    fitness_score = calculate_fitness(random_schedule)

    print("\n--- KẾT QUẢ LỊCH TRÌNH NGẪU NHIÊN ---")
    sorted_items = sorted(random_schedule.timetable.items())

    # --- THAY ĐỔI NẰM Ở ĐÂY ---
    for (day_idx, start_slot_idx), task in sorted_items:
        day_name = WORKING_DAYS[day_idx]

        # Tính toán giờ bắt đầu
        start_hour = start_slot_idx // 2
        start_minute = (start_slot_idx % 2) * 30

        # Tính toán giờ kết thúc
        end_slot_idx = start_slot_idx + task.duration
        end_hour = end_slot_idx // 2
        end_minute = (end_slot_idx % 2) * 30

        print(
            f"[{day_name}] {start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d} -> {task.name}"
        )

    print(f"\n>>> ĐIỂM FITNESS CỦA LỊCH TRÌNH: {fitness_score:.2f}")