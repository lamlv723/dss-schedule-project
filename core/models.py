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