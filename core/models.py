# Giả định 1 slot = 30 phút
SLOTS_PER_DAY = 48
WORKING_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Khung giờ làm việc: 8h sáng (slot 16) đến 5h chiều (slot 34)
WORK_START_SLOT = 16 
WORK_END_SLOT = 34

class Task:
    """
    Đại diện cho một công việc hoặc môn học cần được xếp lịch.
    """
    def __init__(self, name, duration, priority=1):
        """
        Khởi tạo một công việc.
        - name (str): Tên công việc (VD: "Học Toán").
        - duration (int): Thời lượng cần thiết, tính bằng số slot (1 slot = 30 phút).
        - priority (int): Mức độ ưu tiên (càng cao càng quan trọng).
        """
        self.name = name
        self.duration = duration
        self.priority = priority

    def __repr__(self):
        """Giúp in ra thông tin của Task một cách rõ ràng."""
        return f"Task(Tên: {self.name}, Thời lượng: {self.duration} slot)"
    

class Schedule:
    """
    Đại diện cho một thời khóa biểu (một "cá thể" trong thuật toán di truyền).
    Đây là một giải pháp khả thi cho bài toán xếp lịch.
    """
    def __init__(self, tasks_to_schedule):
        """
        Khởi tạo một thời khóa biểu.
        - tasks_to_schedule (list[Task]): Danh sách các công việc cần được xếp.
        """
        self.tasks = tasks_to_schedule
        # timetable là một dictionary lưu lịch trình.
        # Key: (ngày, slot_bắt_đầu), Value: Task được gán vào
        self.timetable = {}
        self.fitness = -1 # Điểm để đánh giá độ tốt của lịch trình

    def __repr__(self):
        return f"Schedule(Fitness: {self.fitness})"