# app.py

import streamlit as st
import pandas as pd
from typing import List, Dict
import streamlit.components.v1 as components  # Import the components library
from core.models import Task, Schedule, ScheduledTask
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
            "Tần suất (số lần/tuần)", min_value=1, max_value=7, value=1, step=1,
            help="Số lần công việc này cần được xếp trong tuần."
        )
        submitted = st.form_submit_button("Thêm Công Việc")
        if submitted and name and duration:
            st.session_state.tasks.append(Task(name=name, duration=int(duration), priority=int(priority), frequency=int(frequency)))
            st.success(f"Đã thêm: '{name}'")
    st.divider()
    with st.expander("Thiết lập thuật toán (Nâng cao)"):
        configs.POPULATION_SIZE = st.number_input("Kích thước quần thể", min_value=10, value=configs.POPULATION_SIZE)
        configs.MUTATION_RATE = st.slider("Tỷ lệ đột biến", 0.0, 1.0, value=configs.MUTATION_RATE)
        configs.NUM_GENERATIONS = st.number_input("Số thế hệ", min_value=10, value=configs.NUM_GENERATIONS)
        configs.SLOT_DURATION_MINUTES = st.number_input("Thời lượng mỗi slot (phút)", min_value=15, value=configs.SLOT_DURATION_MINUTES, step=15)
    st.divider()
    st.header("Danh sách công việc")
    if not st.session_state.tasks:
        st.info("Chưa có công việc nào được thêm.")
    else:
        for i, task in enumerate(st.session_state.tasks):
            task_cols = st.columns([8, 1])
            with task_cols[0]:
                with st.expander(f"**{task.name}** ({task.duration} phút, Tần suất: {task.frequency}x)"):
                    with st.form(key=f"edit_form_{i}"):
                        st.subheader(f"Chỉnh sửa: {task.name}")
                        edited_name = st.text_input("Tên công việc", value=task.name)
                        edited_duration = st.number_input("Thời lượng (phút)", min_value=15, value=task.duration, step=15)
                        edited_priority = st.slider("Độ ưu tiên", min_value=1, max_value=5, value=task.priority)
                        edited_frequency = st.number_input("Tần suất", min_value=1, max_value=7, value=task.frequency)
                        if st.form_submit_button("Lưu thay đổi"):
                            st.session_state.tasks[i] = Task(edited_name, int(edited_duration), int(edited_priority), int(edited_frequency))
                            st.rerun()
            with task_cols[1]:
                if st.button("🗑️", key=f"delete_button_{i}", help="Xóa công việc này"):
                    st.session_state.tasks.pop(i)
                    st.rerun()

# --- Cột 2: Tạo và Hiển thị Lịch trình ---
with col2:
    st.header("2. Tạo và Xem Lịch Trình")
    if st.button("Tạo Lịch Trình", type="primary", use_container_width=True):
        if st.session_state.tasks:
            with st.spinner("Đang chạy thuật toán di truyền..."):
                final_schedule, demo_log = run_genetic_algorithm(st.session_state.tasks)
                st.session_state.schedule = final_schedule
                
                # --- New Logic to Print to Browser Console ---
                # Build the JavaScript code string from the log messages
                js_log_messages = ""
                for message in demo_log:
                    # Escape backticks and wrap the message in backticks for JS template literals
                    js_message = message.replace("`", "\\`")
                    js_log_messages += f'console.log(`{js_message}`);\n'
                
                # Create the full script and execute it
                if js_log_messages:
                    components.html(f"<script>{js_log_messages}</script>", height=0)

                st.success("Tạo lịch trình thành công! (Mở console của trình duyệt để xem chi tiết demo)")
        else:
            st.warning("Vui lòng thêm ít nhất một công việc.")

    st.divider()

    # The calendar display logic remains the same
    if st.session_state.schedule and st.session_state.schedule.scheduled_tasks:
        st.subheader("Lịch trình tối ưu của bạn")
        tasks_by_day: Dict[int, List[ScheduledTask]] = {i: [] for i in range(7)}
        for stask in st.session_state.schedule.scheduled_tasks:
            tasks_by_day[stask.day].append(stask)
        for day in tasks_by_day:
            tasks_by_day[day].sort(key=lambda st: st.start_time)
        days_of_week = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ Nhật"]
        cols = st.columns(7)
        for i, col in enumerate(cols):
            with col:
                st.markdown(f"**<p style='text-align: center;'>{days_of_week[i]}</p>**", unsafe_allow_html=True)
                st.markdown("---")
                if not tasks_by_day[i]:
                    st.info("Trống")
                else:
                    for stask in tasks_by_day[i]:
                        start_mins = stask.start_time * configs.SLOT_DURATION_MINUTES
                        start_time_str = f"{start_mins // 60:02d}:{start_mins % 60:02d}"
                        st.info(f"**{stask.task.name}**\n\n🕒 {start_time_str} ({stask.task.duration} phút)")
    elif st.session_state.schedule:
        st.info("Thuật toán không xếp được công việc nào.")
    else:
        st.info("Nhấn nút 'Tạo Lịch Trình' để xem kết quả.")