from core.models import Task, WORKING_DAYS
from core.algorithm import run_genetic_algorithm

# --- Các tham số cho thuật toán ---
POPULATION_SIZE = 200   # Số lượng lịch trình trong một quần thể
GENERATIONS = 100      # Số thế hệ sẽ "tiến hóa"
MUTATION_RATE = 0.2  # Tỷ lệ đột biến trong thuật toán di truyền

if __name__ == "__main__":

    all_tasks = [
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

    print("--- BẮT ĐẦU QUÁ TRÌNH TIẾN HÓA ---")
    best_schedule_found = run_genetic_algorithm(
        tasks_to_schedule=all_tasks,
        population_size=POPULATION_SIZE,
        generations=GENERATIONS,
        mutation_rate=MUTATION_RATE
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