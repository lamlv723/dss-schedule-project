from core.models import Task, Schedule

if __name__ == "__main__":
    # 1. Định nghĩa danh sách các công việc cần xếp
    all_tasks = [
        Task(name="Làm đồ án DSS", duration=4, priority=3),
        Task(name="Học Tiếng Anh", duration=2, priority=2),
        Task(name="Tập thể dục", duration=2, priority=1),
        Task(name="Họp nhóm", duration=3, priority=3),
    ]

    # 2. Tạo một đối tượng Schedule từ danh sách công việc
    schedule_instance = Schedule(tasks_to_schedule=all_tasks)

    print("Đã tạo thành công các đối tượng:")
    print("Danh sách công việc:")
    for task in schedule_instance.tasks:
        print(f"- {task}")

    print("\nMột bản thể Lịch trình (Schedule) ban đầu:")
    print(schedule_instance)