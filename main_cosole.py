from core.models import Task

if __name__ == "__main__":
    task1 = Task(name="Làm đồ án DSS", duration=4, priority=3)
    task2 = Task(name="Học Tiếng Anh", duration=2, priority=2)
    
    print("Đã tạo thành công các đối tượng Task từ cấu trúc mới:")
    print(task1)
    print(task2)