import streamlit as st
from datetime import time
import pandas as pd
from streamlit_calendar import calendar
from datetime import datetime, timedelta

# --- IMPORT CORE MODULE ---
from core.models import Task, Schedule, BlockedTimeSlot
from core.algorithm import run_genetic_algorithm
from core import configs


st.set_page_config(layout="wide") # Sử dụng toàn bộ chiều rộng trang

st.title("Trợ lý Xếp lịch Thông minh 🧠")
st.write("Ứng dụng này sử dụng Thuật toán Di truyền để tự động tìm kiếm lịch trình tối ưu cho bạn.")

# --- Cấu hình trên Sidebar ---
st.sidebar.header("⚙️ Cấu hình Thuật toán")

population_size = st.sidebar.slider(
    "Kích thước Quần thể (Population Size)", 
    min_value=50, 
    max_value=500, 
    value=configs.POPULATION_SIZE, 
    step=10,
    help="Số lượng lịch trình được tạo ra trong mỗi thế hệ. Càng lớn càng có khả năng tìm ra giải pháp tốt hơn, nhưng chạy lâu hơn."
)

generations = st.sidebar.slider(
    "Số Thế hệ (Generations)", 
    min_value=50, 
    max_value=1000, 
    value=configs.GENERATIONS, 
    step=20,
    help="Số vòng lặp 'tiến hóa'. Càng nhiều thế hệ, kết quả càng có thể tốt hơn."
)

k_crossover = st.sidebar.slider(
    "Hệ số Lai ghép (K Crossover)", 
    min_value=0.1, 
    max_value=1.0, 
    value=configs.ADAPTIVE_K_CROSSOVER, 
    step=0.05,
    help="Hệ số k cho tỷ lệ lai ghép thích ứng."
)

k_mutation = st.sidebar.slider(
    "Hệ số Đột biến (K Mutation)", 
    min_value=0.1, 
    max_value=1.0, 
    value=configs.ADAPTIVE_K_MUTATION, 
    step=0.05,
    help="Hệ số k cho tỷ lệ đột biến thích ứng."
)


# --- Khu vực quản lý công việc ---
st.header("📝 Danh sách Công việc")

# Khởi tạo danh sách tasks trong session state nếu chưa có
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

# Form để thêm công việc mới
with st.form("new_task_form", clear_on_submit=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_name = st.text_input("Tên công việc")
    with col2:
        duration = st.number_input("Thời lượng (30 phút/slot)", min_value=1, value=2)
    with col3:
        priority = st.selectbox("Độ ưu tiên", options=[1, 2, 3, 4], help="1 là ưu tiên cao nhất")
    with col4:
        is_work_time = st.checkbox("Trong giờ làm việc?")
    
    submitted = st.form_submit_button("Thêm công việc")
    if submitted and task_name:
        st.session_state.tasks.append({
            "name": task_name,
            "duration": duration,
            "priority": priority,
            "is_work_time": is_work_time
        })

# Hiển thị danh sách công việc hiện tại dưới dạng bảng
if st.session_state.tasks:
    df_tasks = pd.DataFrame(st.session_state.tasks)
    st.dataframe(df_tasks, use_container_width=True)

# Nút để chạy thuật toán
if st.button("Tạo Lịch trình Tối ưu 🚀", type="primary"):
    if not st.session_state.tasks:
        st.warning("Vui lòng thêm ít nhất một công việc để xếp lịch.")
    else:
        # Chuyển đổi tasks từ session state thành đối tượng Task
        tasks_to_schedule = [Task(**task_data) for task_data in st.session_state.tasks]

        # (Bạn cần import Task và các class khác từ core.models)
        # (Bạn cần import run_genetic_algorithm từ core.algorithm)

        with st.spinner("Thuật toán đang làm việc... Quá trình này có thể mất một lúc... ⏳"):
            # Gọi thuật toán của bạn
            # best_schedule = run_genetic_algorithm(...)

            # --- GIẢ LẬP KẾT QUẢ ĐỂ TEST GIAO DIỆN ---
            # (Sau khi có kết quả thật, bạn sẽ thay thế phần này)
            from core.models import ScheduledTask, Task, Schedule
            mock_task_1 = ScheduledTask(task=Task(name="Họp team", duration=2, priority=1), day="Monday", start_slot=18) # 9:00 AM
            mock_task_2 = ScheduledTask(task=Task(name="Làm việc", duration=4, priority=1), day="Tuesday", start_slot=20) # 10:00 AM
            best_schedule = Schedule(scheduled_tasks=[mock_task_1, mock_task_2])
            # --- KẾT THÚC GIẢ LẬP ---

        st.success("Đã tìm thấy lịch trình tối ưu!")

        # Chuyển đổi kết quả thành định dạng mà calendar component yêu cầu
        calendar_events = []
        today = datetime.now()
        # Tìm ngày thứ Hai của tuần hiện tại để làm mốc
        start_of_week = today - timedelta(days=today.weekday()) 

        for stask in best_schedule.scheduled_tasks:
            day_index = configs.DAYS_OF_WEEK.index(stask.day)
            task_date = start_of_week + timedelta(days=day_index)

            start_time = task_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=stask.start_slot * 30)
            end_time = start_time + timedelta(minutes=stask.task.duration * 30)

            calendar_events.append({
                "title": stask.task.name,
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "color": "#FF6B6B" if stask.task.priority == 1 else "#4ECDC4", # Màu sắc theo độ ưu tiên
            })

        # Hiển thị lịch
        st.header("🗓️ Kết quả Lịch trình")
        calendar(events=calendar_events)