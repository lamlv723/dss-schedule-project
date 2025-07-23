# app.py

import streamlit as st
import pandas as pd
from core.models import Task, Schedule
import core.configs as configs
from core.algorithm import run_genetic_algorithm

# --- Cấu hình trang ---
st.set_page_config(
    page_title="Trình Xếp Lịch Thông Minh",
    page_icon="🗓️",
    layout="wide"
)

# --- Khởi tạo Session State ---
if 'tasks' not in st.session_state:
    st.session_state.tasks = []

if 'schedule' not in st.session_state:
    st.session_state.schedule = None

# --- Giao diện chính ---
st.title("🗓️ Trình Xếp Lịch Thông Minh")
st.markdown("""
Ứng dụng này sử dụng thuật toán di truyền để tìm ra lịch trình tối ưu cho các công việc của bạn.
Hãy thêm các công việc ở cột bên trái, sau đó nhấn nút "Tạo Lịch Trình".
""")

# --- Bố cục giao diện ---
col1, col2 = st.columns([1, 2])

# --- Cột 1: Nhập liệu và Cấu hình ---
with col1:
    st.header("1. Thêm Công Việc")

    with st.form(key="add_task_form", clear_on_submit=True):
        name = st.text_input("Tên công việc", placeholder="Ví dụ: Họp nhóm hàng tuần")
        duration = st.number_input("Thời lượng (phút)", min_value=15, value=60, step=15)
        priority = st.slider("Độ ưu tiên (5 là cao nhất)", min_value=1, max_value=5, value=3)
        
        frequency = st.number_input(
            "Tần suất (số lần/tuần)", 
            min_value=1, 
            max_value=7, 
            value=1,
            step=1,
            help="Số lần công việc này cần được xếp trong tuần."
        )

        submitted = st.form_submit_button("Thêm Công Việc")

        if submitted:
            if name and duration:
                new_task = Task(
                    name=name,
                    duration=int(duration),
                    priority=int(priority),
                    frequency=int(frequency)
                )
                st.session_state.tasks.append(new_task)
                st.success(f"Đã thêm công việc: '{name}'")
            else:
                st.error("Vui lòng nhập tên và thời lượng công việc.")

    st.divider()

    with st.expander("Thiết lập thuật toán (Nâng cao)"):
        configs.POPULATION_SIZE = st.number_input(
            "Kích thước quần thể", 
            min_value=10, 
            value=configs.POPULATION_SIZE
        )
        configs.MUTATION_RATE = st.slider(
            "Tỷ lệ đột biến",
            min_value=0.0,
            max_value=1.0,
            value=configs.MUTATION_RATE
        )
        configs.NUM_GENERATIONS = st.number_input(
            "Số thế hệ",
            min_value=10,
            value=configs.NUM_GENERATIONS
        )
        
        # --- Restored Code Block ---
        # This input for SLOT_DURATION_MINUTES is now back.
        configs.SLOT_DURATION_MINUTES = st.number_input(
            "Thời lượng mỗi slot (phút)",
            min_value=15,
            value=configs.SLOT_DURATION_MINUTES,
            step=15,
            help="Chia một ngày thành các khoảng thời gian nhỏ."
        )
        # --- End of Restored Code ---

    st.divider()

    st.header("Danh sách công việc")
    if not st.session_state.tasks:
        st.info("Chưa có công việc nào được thêm.")
    else:
        for i, task in enumerate(st.session_state.tasks):
            st.write(
                f"{i + 1}. **{task.name}** - "
                f"{task.duration} phút, "
                f"Ưu tiên: {task.priority}, "
                f"Tần suất: {task.frequency} lần"
            )

# --- Cột 2: Tạo và Hiển thị Lịch trình ---
with col2:
    st.header("2. Tạo và Xem Lịch Trình")

    if st.button("Tạo Lịch Trình", type="primary", use_container_width=True):
        if st.session_state.tasks:
            with st.spinner("Đang chạy thuật toán di truyền... Việc này có thể mất một lúc."):
                final_schedule = run_genetic_algorithm(st.session_state.tasks)
                st.session_state.schedule = final_schedule
                st.success("Tạo lịch trình thành công!")
        else:
            st.warning("Vui lòng thêm ít nhất một công việc để tạo lịch trình.")

    st.divider()

    if st.session_state.schedule and st.session_state.schedule.scheduled_tasks:
        st.subheader("Lịch trình tối ưu của bạn")
        
        schedule_data = []
        for scheduled_task in st.session_state.schedule.scheduled_tasks:
            start_mins = scheduled_task.start_time * configs.SLOT_DURATION_MINUTES
            end_mins = start_mins + scheduled_task.task.duration
            start_time_str = f"{start_mins // 60:02d}:{start_mins % 60:02d}"
            end_time_str = f"{end_mins // 60:02d}:{end_mins % 60:02d}"
            time_frame = f"{start_time_str} - {end_time_str}"

            schedule_data.append({
                "Khung giờ": time_frame,
                "Ngày": ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"][scheduled_task.day],
                "Công việc": scheduled_task.task.name,
            })
        
        df = pd.DataFrame(schedule_data)
        
        calendar_df = df.pivot_table(
            index="Khung giờ", 
            columns="Ngày", 
            values="Công việc", 
            aggfunc='first',
        ).fillna('')
        
        days_order = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        calendar_df = calendar_df.reindex(columns=days_order, fill_value='')
        calendar_df = calendar_df.sort_index()
        
        st.dataframe(calendar_df, use_container_width=True, height=800)

    elif st.session_state.schedule:
        st.info("Thuật toán không xếp được công việc nào. Hãy thử lại với ít công việc hơn hoặc giảm thời lượng của chúng.")
    else:
        st.info("Nhấn nút 'Tạo Lịch Trình' để xem kết quả.")