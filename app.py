import streamlit as st
import pandas as pd
from datetime import time, datetime, timedelta
from streamlit_calendar import calendar

# --- IMPORT CORE MODULE ---
from core.models import Task, Schedule, BlockedTimeSlot, ScheduledTask
from core.algorithm import run_genetic_algorithm
from core import configs

st.set_page_config(layout="wide")

st.title("Trợ lý Xếp lịch Thông minh 🧠")
st.write("Ứng dụng này sử dụng Thuật toán Di truyền để tự động tìm kiếm lịch trình tối ưu cho bạn.")

# --- Cấu hình trên Sidebar ---
st.sidebar.header("⚙️ Cấu hình Thuật toán")
# (Các slider cấu hình của bạn ở đây - không thay đổi)
population_size = st.sidebar.slider(
    "Kích thước Quần thể (Population Size)", 
    min_value=50, 
    max_value=500, 
    value=configs.POPULATION_SIZE, 
    step=10
)
generations = st.sidebar.slider(
    "Số Thế hệ (Generations)", 
    min_value=50, 
    max_value=1000, 
    value=configs.GENERATIONS, 
    step=20
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

# --- Khởi tạo Session State ---
# Cần khởi tạo các key trước để tránh lỗi
if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'best_schedule' not in st.session_state:
    st.session_state.best_schedule = None

# --- Khu vực quản lý công việc ---
st.header("📝 Danh sách Công việc")
with st.form("new_task_form", clear_on_submit=True):
    # (Code form thêm task của bạn ở đây - không thay đổi)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        task_name = st.text_input("Tên công việc")
    with col2:
        duration = st.number_input("Thời lượng (30 phút/slot)", min_value=1, value=2)
    with col3:
        priority = st.selectbox("Độ ưu tiên", range(1, configs.TOTAL_PRIORITY_LEVELS + 1), help="1 là ưu tiên cao nhất")
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
        # Reset lại lịch trình cũ khi có task mới được thêm
        st.session_state.best_schedule = None

# Hiển thị danh sách công việc hiện tại
# DF version
# if st.session_state.tasks:
#     st.dataframe(pd.DataFrame(st.session_state.tasks), use_container_width=True)

# Hiển thị danh sách công việc hiện tại dưới dạng bảng có thể chỉnh sửa
if st.session_state.tasks:
    st.write("### Danh sách công việc hiện tại")
    # Chuyển đổi list of dicts thành DataFrame
    df_tasks = pd.DataFrame(st.session_state.tasks)
    
    # Thêm một cột 'delete' với giá trị mặc định là False
    df_tasks['delete'] = False
    
    # Sử dụng st.data_editor để tạo bảng có thể tương tác
    edited_df = st.data_editor(
        df_tasks,
        column_config={
            "name": st.column_config.TextColumn("Tên công việc"),
            "duration": st.column_config.NumberColumn("Thời lượng (slots)"),
            "priority": st.column_config.SelectboxColumn("Độ ưu tiên", options=range(1, configs.TOTAL_PRIORITY_LEVELS + 1)),
            "is_work_time": st.column_config.CheckboxColumn("Trong giờ?"),
            "delete": st.column_config.CheckboxColumn("Xóa?") # Cột để chọn xóa
        },
        use_container_width=True,
        hide_index=True,
    )

    # Nút để xác nhận việc xóa
    if st.button("Cập nhật danh sách công việc"):
        # Lọc ra những hàng không được đánh dấu xóa
        remaining_tasks_df = edited_df[edited_df["delete"] == False]
        # Chuyển DataFrame trở lại thành list of dicts và cập nhật session_state
        st.session_state.tasks = remaining_tasks_df.drop(columns=['delete']).to_dict('records')
        # Reset lại lịch trình cũ vì danh sách task đã thay đổi
        st.session_state.best_schedule = None
        st.rerun() # Chạy lại app để cập nhật bảng

# --- Nút chạy thuật toán & Logic xử lý ---
if st.button("Tạo Lịch trình Tối ưu 🚀", type="primary"):
    if not st.session_state.tasks:
        st.warning("Vui lòng thêm ít nhất một công việc để xếp lịch.")
    else:
        tasks_to_schedule = [Task(**task_data) for task_data in st.session_state.tasks]
        with st.spinner("Thuật toán đang làm việc... Quá trình này có thể mất một lúc... ⏳"):
            # CHẠY THUẬT TOÁN THẬT
            # Ghi đè kết quả vào session_state
            st.session_state.best_schedule = run_genetic_algorithm(
                tasks_to_schedule=tasks_to_schedule,
                population_size=population_size,
                generations=generations,
                blocked_slots=configs.blocked_slots
            )
        st.success("Đã tìm thấy lịch trình tối ưu!")

# --- Hiển thị kết quả (LUÔN KIỂM TRA TỪ SESSION STATE) ---
if st.session_state.best_schedule:
    st.header("🗓️ Kết quả Lịch trình")
    
    calendar_events = []
    today = datetime.now()
    start_of_week = today - timedelta(days=today.weekday())

    for stask in st.session_state.best_schedule.scheduled_tasks:
        day_index = configs.DAYS_OF_WEEK.index(stask.day)
        task_date = start_of_week + timedelta(days=day_index)
        
        start_time = task_date.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(minutes=stask.start_slot * 30)
        end_time = start_time + timedelta(minutes=stask.task.duration * 30)

        calendar_events.append({
            "title": stask.task.name,
            "start": start_time.isoformat(),
            "end": end_time.isoformat(),
            "color": "#FF6B6B" if stask.task.priority == 1 else "#4ECDC4",
        })

    # Tùy chọn để hiển thị lịch theo định dạng 24 giờ
    calendar_options = {
        "headerToolbar": {
            "left": "prev,next today",
            "center": "title",
            "right": "dayGridMonth,timeGridWeek,timeGridDay",
        },
        "slotMinTime": "00:00:00",
        "slotMaxTime": "24:00:00",
        "initialView": "timeGridWeek", # Chế độ xem mặc định là tuần
        "allDaySlot": False, # Ẩn dòng "all-day"
        "eventTimeFormat": { # Định dạng thời gian hiển thị trên sự kiện
            "hour": "2-digit",
            "minute": "2-digit",
            "hour12": False
        }
    }
        
    calendar(events=calendar_events, options=calendar_options)