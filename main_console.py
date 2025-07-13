from core.models import Task, WORKING_DAYS
from core.algorithm import run_genetic_algorithm

# --- Các tham số cho thuật toán ---
POPULATION_SIZE = 50   # Số lượng lịch trình trong một quần thể
GENERATIONS = 100      # Số thế hệ sẽ "tiến hóa"

if __name__ == "__main__":
    all_tasks = [
        # Các công việc TRONG GIỜ (bắt buộc phải ghi is_work_time=True)
        Task(name="Làm đồ án DSS", duration=4, priority=3, is_work_time=True),
        Task(name="Họp nhóm", duration=3, priority=3, is_work_time=True),

        # Các công việc NGOÀI GIỜ (mặc định là is_work_time=False)
        Task(name="Tập thể dục", duration=2, priority=1),
        Task(name="Đọc sách", duration=2, priority=1),
        Task(name="Học Tiếng Anh", duration=3, priority=2),
        Task(name="Dọn dẹp nhà", duration=3, priority=2),
    ]

    print("--- BẮT ĐẦU QUÁ TRÌNH TIẾN HÓA ---")
    best_schedule_found = run_genetic_algorithm(
        tasks_to_schedule=all_tasks,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS
    )

    print("\n--- LỊCH TRÌNH TỐI ƯU NHẤT ĐƯỢC TÌM THẤY ---")

    sorted_items = sorted(best_schedule_found.timetable.items())
    
    for (day_idx, start_slot_idx), task in sorted_items:
        day_name = WORKING_DAYS[day_idx]
        
        start_hour = start_slot_idx // 2
        start_minute = (start_slot_idx % 2) * 30
        
        end_slot_idx = start_slot_idx + task.duration
        end_hour = end_slot_idx // 2
        end_minute = (end_slot_idx % 2) * 30
        
        task_type = "Trong giờ" if task.is_work_time else "Ngoài giờ"
        print(
            f"[{day_name}] ({task_type}) {start_hour:02d}:{start_minute:02d} - {end_hour:02d}:{end_minute:02d} -> {task.name}"
        )

    print(f"\n>>> ĐIỂM FITNESS CUỐI CÙNG: {best_schedule_found.fitness:.2f}")