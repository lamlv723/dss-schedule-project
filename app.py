# app.py

import streamlit as st
import pandas as pd
import json
from datetime import datetime, time

from config import app_config, ga_config 
from ga_core.engine import run_ga_optimization
from ga_core import chromosome
from utils.helpers import convert_schedule_to_dataframe, parse_blocked_times, create_gantt_chart

def main():
    """
    Main function to run the Streamlit application.
    """
    st.set_page_config(layout="wide")
    st.title("🗓️ Weekly Task Scheduler")

    st.sidebar.header("Configuration")
    
    st.sidebar.subheader("1. Upload Your Tasks")
    uploaded_file = st.sidebar.file_uploader(
        "Upload a JSON file with your tasks", type=["json"]
    )

    sample_tasks_file = "./data/sample_tasks.json" 

    try:
        if uploaded_file is not None:
            tasks = json.load(uploaded_file)
            st.sidebar.success(f"Successfully loaded {len(tasks)} tasks!")
        else:
            st.sidebar.info("Using sample tasks. Upload a file above to use your own data.")
            with open(sample_tasks_file, 'r') as f:
                tasks = json.load(f)
    except (json.JSONDecodeError, KeyError, FileNotFoundError) as e:
        st.sidebar.error(f"Error reading tasks file: {e}")
        return

    st.sidebar.subheader("2. Set Genetic Algorithm Parameters")
    ga_config.POPULATION_SIZE = st.sidebar.slider(
        "Population Size", 10, 500, ga_config.POPULATION_SIZE, 10
    )
    ga_config.N_GENERATIONS = st.sidebar.slider(
        "Number of Generations", 10, 1000, ga_config.N_GENERATIONS, 10
    )
    ga_config.MUTATION_PROBABILITY = st.sidebar.slider(
        "Mutation Probability", 0.01, 1.0, ga_config.MUTATION_PROBABILITY, 0.01
    )
    ga_config.CROSSOVER_PROBABILITY = st.sidebar.slider(
        "Crossover Probability", 0.1, 1.0, ga_config.CROSSOVER_PROBABILITY, 0.05
    )
    ga_config.ELITE_SIZE = st.sidebar.slider(
        "Elite Size (how many top solutions to keep)", 1, 10, int(ga_config.POPULATION_SIZE * 0.1), 1
    )

    st.sidebar.subheader("3. Define Blocked Time Slots")
    blocked_times_str = st.sidebar.text_area(
        "Blocked Times", value=app_config.DEFAULT_BLOCKED_TIMES, height=200
    )
    
    try:
        blocked_slots = parse_blocked_times(blocked_times_str)
    except Exception as e:
        st.sidebar.error(f"Error parsing blocked times: {e}")
        return

    st.header("Tasks to be Scheduled")
    tasks_df = pd.DataFrame(tasks)
    st.dataframe(tasks_df, use_container_width=True)

    if st.button("Generate Schedule", type="primary"):
        with st.spinner("The Genetic Algorithm is thinking... This may take a moment."):
            
            task_instances = []
            for i, task in enumerate(tasks):
                instance = task.copy()
                instance['instance_id'] = f"task_{i}"
                instance['original_id'] = task.get('id', i)
                task_instances.append(instance)
            
            tasks_map = {task['instance_id']: task for task in task_instances}

            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def progress_callback(progress_value, message):
                progress_bar.progress(progress_value)
                status_text.text(message)

            best_individual, logbook = run_ga_optimization(
                tasks_map=tasks_map,
                task_instances=task_instances,
                blocked_slots=blocked_slots,
                progress_callback=progress_callback
            )

            st.header("Optimal Schedule Found")
            
            final_schedule = best_individual[0]
            final_fitness = final_schedule.fitness.values[0]

            col1, col2, col3 = st.columns(3)
            col1.metric("Final Fitness Score", f"{final_fitness:.4f}")
            col2.metric("Total Tasks Scheduled", f"{len(final_schedule)}")
            col3.metric("Generations Run", f"{ga_config.N_GENERATIONS}")

            # <<< FIX: Lịch trình không hợp lệ có fitness là 0.0 trong bài toán tối đa hóa
            if not final_schedule or final_fitness == 0.0:
                st.warning("No valid schedule could be found. Try increasing generations, population size, or adjusting task constraints.")
            else:
                schedule_df = convert_schedule_to_dataframe(final_schedule, tasks_map)
                
                fig = create_gantt_chart(schedule_df)
                st.plotly_chart(fig, use_container_width=True)

                st.subheader("Schedule Details")
                st.dataframe(schedule_df.sort_values(by="Start").reset_index(drop=True), use_container_width=True)
                
                st.subheader("Optimization Log")
                log_df = pd.DataFrame(logbook)
                log_df = log_df[['gen', 'avg', 'min', 'max']]
                st.dataframe(log_df, use_container_width=True)

if __name__ == "__main__":
    main()