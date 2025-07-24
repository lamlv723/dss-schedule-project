# app.py

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from typing import List, Dict, Any, Union, Optional

# Import project modules
from config import app_config, ga_config
from ga_core.engine import run_ga_optimization
from ga_core import chromosome
from utils.helpers import convert_schedule_to_dataframe, parse_blocked_times, create_gantt_chart

# --- Helper functions for session state and data conversion ---

def string_to_date_obj(date_str: Optional[str]) -> Optional[datetime.date]:
    """Converts an ISO format string to a datetime.date object, returns None if invalid."""
    if not date_str or not isinstance(date_str, str):
        return None
    try:
        return datetime.fromisoformat(date_str.split('T')[0]).date()
    except (ValueError, TypeError):
        return None

def initialize_session_state() -> None:
    """Initializes the session state for storing tasks if it doesn't exist."""
    if 'tasks' not in st.session_state:
        st.session_state.tasks: List[Dict[str, Any]] = [
            {
                "id": 1, 
                "name": "Soạn báo cáo tuần", 
                "estimated_time_hr": 2.0, 
                "priority": 1, 
                "category": "Công việc",
                "predecessor_task_id": None,
                "deadline": "2025-07-28",
                "earliest_start_time": "2025-07-25"
            }
        ]

def add_task() -> None:
    """Adds a new, empty task to the session state."""
    max_id = max([task['id'] for task in st.session_state.tasks] or [0])
    new_task_id = max_id + 1
    st.session_state.tasks.append({
        "id": new_task_id, "name": "", "estimated_time_hr": 1.0, "priority": 3, "category": "",
        "predecessor_task_id": None, "deadline": None, "earliest_start_time": None
    })

def delete_task(task_id_to_delete: int) -> None:
    """Deletes a task from the session state by its ID."""
    st.session_state.tasks = [
        task for task in st.session_state.tasks if task['id'] != task_id_to_delete
    ]

# --- Main App Function ---

def main() -> None:
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(layout="wide")
    st.title("Lập Lịch Công Việc Tuần Bằng Thuật Toán Di Truyền")

    initialize_session_state()

    # --- Sidebar for GA configuration ---
    st.sidebar.header("Cấu hình Thuật toán")
    
    ga_config.POPULATION_SIZE = st.sidebar.slider(
        "Kích thước quần thể (Population Size)", 10, 500, ga_config.POPULATION_SIZE, 10
    )
    ga_config.N_GENERATIONS = st.sidebar.slider(
        "Số thế hệ (Generations)", 10, 1000, ga_config.N_GENERATIONS, 10
    )
    ga_config.MUTATION_PROBABILITY = st.sidebar.slider(
        "Tỷ lệ đột biến (Mutation Probability)", 0.01, 1.0, ga_config.MUTATION_PROBABILITY, 0.01
    )
    ga_config.CROSSOVER_PROBABILITY = st.sidebar.slider(
        "Tỷ lệ lai ghép (Crossover Probability)", 0.1, 1.0, ga_config.CROSSOVER_PROBABILITY, 0.05
    )
    # <<< FIX: Restored the Elite Size slider
    ga_config.ELITE_SIZE = st.sidebar.slider(
        "Elite Size (how many top solutions to keep)", 1, 10, int(ga_config.POPULATION_SIZE * 0.1), 1
    )
    
    st.sidebar.subheader("Cấu hình Ràng buộc")
    blocked_times_str = st.sidebar.text_area(
        "Khung giờ bận", value=app_config.DEFAULT_BLOCKED_TIMES, height=200
    )
    
    try:
        blocked_slots = parse_blocked_times(blocked_times_str)
    except Exception as e:
        st.sidebar.error(f"Lỗi xử lý khung giờ bận: {e}")
        st.stop()

    # --- Main Screen Area ---
    st.header("Tùy chọn Nhập liệu Công việc")
    
    input_tab1, input_tab2 = st.tabs(["Tải lên tệp JSON", "Nhập thủ công"])

    submitted_from_form = False
    with input_tab1:
        st.subheader("1. Tải lên tệp JSON")
        uploaded_file = st.file_uploader(
            "Tải lên tệp JSON chứa các công việc", type=["json"], label_visibility="collapsed"
        )

    with input_tab2:
        st.subheader("2. Hoặc Nhập Công việc Thủ công")

        header_cols = st.columns([0.5, 3, 1, 1, 2, 1.5, 2, 2, 0.5])
        header_cols[0].markdown("**ID**")
        header_cols[1].markdown("**Tên công việc**")
        header_cols[2].markdown("**Thời gian (giờ)**")
        header_cols[3].markdown("**Ưu tiên**")
        header_cols[4].markdown("**Danh mục**")
        header_cols[5].markdown("**Việc tiên quyết**")
        header_cols[6].markdown("**Deadline**")
        header_cols[7].markdown("**Bắt đầu sớm nhất**")
        header_cols[8].markdown("**Xóa**")
        st.divider()

        all_task_ids = [task['id'] for task in st.session_state.tasks]

        for task in st.session_state.tasks:
            cols = st.columns([0.5, 3, 1, 1, 2, 1.5, 2, 2, 0.5])
            
            cols[0].write(f"#{task['id']}")
            task['name'] = cols[1].text_input("Name", value=task["name"], key=f"name_{task['id']}", label_visibility="collapsed")
            task['estimated_time_hr'] = cols[2].number_input("Time (hr)", value=float(task["estimated_time_hr"]), min_value=0.5, step=0.5, format="%.1f", key=f"time_{task['id']}", label_visibility="collapsed")
            task['priority'] = cols[3].selectbox("Priority", options=[1, 2, 3], index=task["priority"] - 1, key=f"priority_{task['id']}", label_visibility="collapsed")
            task['category'] = cols[4].text_input("Category", value=task["category"], key=f"category_{task['id']}", label_visibility="collapsed")

            predecessor_options = [None] + [tid for tid in all_task_ids if tid != task['id']]
            current_predecessor_index = predecessor_options.index(task['predecessor_task_id']) if task['predecessor_task_id'] in predecessor_options else 0
            task['predecessor_task_id'] = cols[5].selectbox("Predecessor", options=predecessor_options, index=current_predecessor_index, key=f"pred_{task['id']}", label_visibility="collapsed")

            deadline_date_obj = cols[6].date_input("Deadline", value=string_to_date_obj(task["deadline"]), key=f"deadline_{task['id']}", label_visibility="collapsed")
            task['deadline'] = f"{deadline_date_obj.isoformat()}T23:59:59" if deadline_date_obj else None

            estart_date_obj = cols[7].date_input("Earliest Start", value=string_to_date_obj(task["earliest_start_time"]), key=f"estart_{task['id']}", label_visibility="collapsed")
            task['earliest_start_time'] = f"{estart_date_obj.isoformat()}T00:00:00" if estart_date_obj else None

            cols[8].button("🗑️", key=f"delete_{task['id']}", on_click=delete_task, args=(task['id'],))

        st.divider()
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("+ Thêm công việc mới", on_click=add_task, use_container_width=True)
        with col2:
            if st.button("Sử dụng các công việc đã nhập", type="primary", use_container_width=True):
                submitted_from_form = True

    # --- Task Loading Logic ---
    tasks: Optional[List[Dict[str, Any]]] = None
    final_tasks_for_ga: List[Dict[str, Any]] = []

    if uploaded_file is not None:
        try:
            tasks = json.load(uploaded_file)
            st.sidebar.success(f"Đã tải lên {len(tasks)} công việc!")
        except (json.JSONDecodeError, KeyError) as e:
            st.sidebar.error(f"Lỗi đọc tệp: {e}")
            st.stop()
    elif submitted_from_form:
        tasks = st.session_state.tasks
        st.sidebar.success(f"Đã nhận {len(tasks)} công việc từ form!")
    else:
        st.sidebar.info("Sử dụng dữ liệu mẫu. Hãy tải tệp lên hoặc nhập thủ công.")
        try:
            with open("./data/sample_tasks.json", 'r', encoding='utf-8') as f:
                tasks = json.load(f)
        except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
            st.sidebar.error(f"Lỗi đọc tệp mẫu: {e}")
            st.stop()
    
    # --- Final Task Processing and Display ---
    if tasks:
        for task in tasks:
            processed_task = task.copy()
            time_in_hours = processed_task.pop('estimated_time_hr', task.get('estimated_time'))
            if time_in_hours is not None:
                try:
                    slots = int(float(time_in_hours) * 60 / app_config.TIME_SLOT_DURATION)
                    processed_task['estimated_time'] = max(1, slots)
                except (ValueError, TypeError):
                    processed_task['estimated_time'] = 1
            
            for key in ['predecessor_task_id', 'deadline', 'earliest_start_time']:
                if not processed_task.get(key):
                    processed_task[key] = None
            final_tasks_for_ga.append(processed_task)
        
        st.header("Các công việc cần sắp xếp")
        st.dataframe(pd.DataFrame(final_tasks_for_ga), use_container_width=True)
    
        if st.button("Tạo Lịch Trình", type="primary", use_container_width=True):
            if final_tasks_for_ga:
                with st.spinner("Thuật toán di truyền đang tính toán..."):
                    
                    task_instances: List[Dict[str, Any]] = []
                    for i, task_data in enumerate(final_tasks_for_ga):
                        instance = task_data.copy()
                        instance['instance_id'] = f"task_{i}"
                        instance['original_id'] = task_data.get('id', i)
                        task_instances.append(instance)
                    
                    tasks_map: Dict[str, Dict[str, Any]] = {task['instance_id']: task for task in task_instances}

                    progress_bar = st.progress(0.0, text="Bắt đầu...")
                    status_text = st.empty()
                    
                    def progress_callback(progress_value: float, message: str) -> None:
                        progress_bar.progress(progress_value)
                        status_text.text(message)

                    best_individual, logbook = run_ga_optimization(
                        tasks_map=tasks_map,
                        task_instances=task_instances,
                        blocked_slots=blocked_slots,
                        progress_callback=progress_callback
                    )

                    st.header("Đã tìm thấy lịch trình tối ưu")
                    
                    final_schedule = best_individual[0]
                    final_fitness = final_schedule.fitness.values[0]

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Điểm Fitness cuối cùng", f"{final_fitness:,.0f}")
                    col2.metric("Tổng số công việc", f"{len(final_schedule)}")
                    col3.metric("Số thế hệ", f"{ga_config.N_GENERATIONS}")

                    if not final_schedule or final_fitness == 0.0:
                        st.warning("Không tìm thấy lịch trình hợp lệ. Hãy thử tăng số thế hệ, kích thước quần thể, hoặc điều chỉnh các ràng buộc.")
                    else:
                        schedule_df = convert_schedule_to_dataframe(final_schedule, tasks_map)
                        
                        fig = create_gantt_chart(schedule_df)
                        st.plotly_chart(fig, use_container_width=True)

                        st.subheader("Chi tiết Lịch trình")
                        st.dataframe(schedule_df.sort_values(by="Start").reset_index(drop=True), use_container_width=True)
                        
                        st.subheader("Nhật ký Tối ưu hóa")
                        log_df = pd.DataFrame(logbook)
                        log_df = log_df[['gen', 'avg', 'min', 'max']]
                        st.dataframe(log_df, use_container_width=True)
            else:
                st.warning("Không có công việc nào để sắp xếp. Vui lòng tải tệp lên hoặc nhập thủ công.")

if __name__ == "__main__":
    main()