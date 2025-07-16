from core.algorithm import run_genetic_algorithm
from core.models import Schedule, Task
# Import all configurations from the config file
from core import configs

# Helper function to print the schedule (you can customize this)
def print_schedule(schedule: Schedule):
    if not schedule.scheduled_tasks:
        print("Lịch trình trống.")
        return

    # Sort tasks by start time for chronological printing
    sorted_tasks = sorted(schedule.scheduled_tasks, key=lambda x: (configs.DAYS_OF_WEEK.index(x.day), x.start_slot))

    current_day = ""
    for scheduled_task in sorted_tasks:
        if scheduled_task.day != current_day:
            current_day = scheduled_task.day
            print(f"\n--- {current_day} ---")

        start_minutes = scheduled_task.start_slot * 30
        end_minutes = start_minutes + scheduled_task.task.duration * 30
        start_time_str = f"{start_minutes // 60:02d}:{start_minutes % 60:02d}"
        end_time_str = f"{end_minutes // 60:02d}:{end_minutes % 60:02d}"

        time_type = "(Trong giờ)" if scheduled_task.task.is_work_time else "(Ngoài giờ)"
        print(f"[{start_time_str} - {end_time_str}] {time_type} -> {scheduled_task.task.name}")

    print(f"\n>>> ĐIỂM FITNESS CUỐI CÙNG: {schedule.fitness:.2f}")


def main():
    """
    Main entry point for the scheduling application.
    This is where you define the INPUT (the list of tasks) and run the algorithm.
    """
    # ======================== TASK DEFINITIONS (INPUT) ========================
    tasks_to_schedule = [
        # --- Công việc ưu tiên cao (Dự án Alpha) ---
        Task(name="[Alpha] Lên kế hoạch các mốc quan trọng", duration=2, priority=1, is_work_time=True),
        Task(name="[Alpha] Phát triển tính năng cốt lõi", duration=6, priority=1, is_work_time=True),
        Task(name="[Alpha] Viết tài liệu kỹ thuật", duration=3, priority=2, is_work_time=True),
        Task(name="[Alpha] Họp đánh giá với team", duration=2, priority=2, is_work_time=True),

        # --- Công việc thông thường ---
        Task(name="Kiểm tra và trả lời email", duration=2, priority=3, is_work_time=True),
        Task(name="Chuẩn bị báo cáo tuần", duration=3, priority=3, is_work_time=True),

        # --- Việc cá nhân ưu tiên cao ---
        Task(name="Đi tập gym", duration=3, priority=1),
        Task(name="Đặt lịch hẹn bác sĩ", duration=1, priority=1),

        # --- Việc cá nhân ưu tiên trung bình ---
        Task(name="Học lấy chứng chỉ", duration=4, priority=2),
        Task(name="Thanh toán hóa đơn hàng tháng", duration=1, priority=2),

        # --- Việc cá nhân ưu tiên thấp ---
        Task(name="Đi mua sắm thực phẩm", duration=3, priority=4),
        Task(name="Dọn dẹp căn hộ", duration=4, priority=4),
        Task(name="Đọc sách", duration=2, priority=4),
    ]

    print("--- BẮT ĐẦU THUẬT TOÁN XẾP LỊCH ---")
    print(f"Tổng số công việc cần xếp: {len(tasks_to_schedule)}")
    
    # The algorithm now implicitly uses constants from the configs file
    best_schedule = run_genetic_algorithm(
        tasks_to_schedule=tasks_to_schedule,
        population_size=configs.POPULATION_SIZE,
        generations=configs.GENERATIONS,
        mutation_rate=configs.MUTATION_RATE,
        blocked_slots=configs.blocked_slots # Pass blocked_slots to the algorithm
    )

    print("\n--- HOÀN TẤT ---")
    if best_schedule:
        print_schedule(best_schedule)
    else:
        print("Không tìm thấy lịch trình phù hợp.")

if __name__ == "__main__":
    main()