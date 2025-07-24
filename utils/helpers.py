# utils/helpers.py

import json
import pandas as pd
from datetime import datetime, timedelta
from config import app_config
import plotly.express as px

def load_tasks_from_json(filepath):
    """Parses the user-provided JSON file into a list of task dictionaries."""
    try:
        with open(filepath, 'r') as f:
            tasks = json.load(f)
        return tasks
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading tasks from {filepath}: {e}")
        return []
    
def create_gantt_chart(schedule_df):
    """Creates a Plotly Gantt chart from a schedule DataFrame."""
    if schedule_df.empty:
        return px.timeline()

    fig = px.timeline(
        schedule_df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Category",
        hover_name="Task",
        labels={"Task": "Task Name"},
        title="Scheduled Tasks Gantt Chart"
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='LightGray')
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='LightGray', categoryorder="total ascending")
    
    fig.update_layout(xaxis_title="Timeline", yaxis_title="Tasks")
    
    return fig

def parse_blocked_times(blocked_times_str):
    """Parses the user's text input for blocked times into a set of blocked slot indices."""
    blocked_slots = set()
    lines = blocked_times_str.strip().split('\n')
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        if len(parts) != 2:
            continue
            
        scope, time_range = parts
        try:
            start_str, end_str = time_range.split('-')
            start_hour, start_minute = map(int, start_str.split(':'))
            end_hour, end_minute = map(int, end_str.split(':'))
        except ValueError:
            # Skip malformed lines
            continue

        start_slot_of_day = (start_hour * 60 + start_minute) // app_config.TIME_SLOT_DURATION
        end_slot_of_day = (end_hour * 60 + end_minute) // app_config.TIME_SLOT_DURATION

        if scope.lower() == 'daily':
            # --- FIX STARTS HERE ---
            # This explicitly handles the overnight case for the very first day
            # before the main loop starts.
            if start_slot_of_day > end_slot_of_day:
                for slot in range(0, end_slot_of_day):
                    blocked_slots.add(slot)
            # --- FIX ENDS HERE ---

            for day in range(app_config.DAYS_IN_SCHEDULE):
                day_offset = day * app_config.SLOTS_PER_DAY
                
                # Standard same-day block
                if start_slot_of_day < end_slot_of_day:
                    for slot in range(start_slot_of_day, end_slot_of_day):
                        blocked_slots.add(day_offset + slot)
                # Overnight block
                else: 
                    # Block from start time to the end of the current day
                    for slot in range(start_slot_of_day, app_config.SLOTS_PER_DAY):
                        blocked_slots.add(day_offset + slot)
                    
                    # Block the next day's morning (if it's within the schedule)
                    if day + 1 < app_config.DAYS_IN_SCHEDULE:
                        next_day_offset = (day + 1) * app_config.SLOTS_PER_DAY
                        for slot in range(0, end_slot_of_day):
                            blocked_slots.add(next_day_offset + slot)

    return blocked_slots


def convert_schedule_to_dataframe(schedule, tasks_map):
    """Transforms the final GA output into a structured Pandas DataFrame for visualization."""
    if not schedule:
        return pd.DataFrame()

    schedule_data = [] # <<< FIX: Initialized as an empty list
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for task_id, start_slot in schedule:
        task_info = tasks_map.get(task_id)
        if not task_info:
            continue

        # Correctly calculate duration in minutes
        duration_in_minutes = task_info.get('estimated_time', 1) * app_config.TIME_SLOT_DURATION
        start_time = start_date + timedelta(minutes=start_slot * app_config.TIME_SLOT_DURATION)
        finish_time = start_time + timedelta(minutes=duration_in_minutes)

        schedule_data.append({
            'Task': task_info.get('name', 'Unnamed Task'),
            'Start': start_time,
            'Finish': finish_time,
            'Deadline': task_info.get('deadline'),
            'Category': task_info.get('category', 'General'),
            'Priority': task_info.get('priority', 99)
        })
    
    df = pd.DataFrame(schedule_data)
    if not df.empty:
        df = df.sort_values(by='Start').reset_index(drop=True)
    return df