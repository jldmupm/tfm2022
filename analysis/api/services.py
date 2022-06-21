from datetime import datetime, timedelta
import pandas as pd

import analysis.sensors.mg_source as mg
import analysis.process.merging as merge_data
import analysis.process.analyze as analyze_data

df_merged = None
df_data_last_time = datetime.utcnow() - timedelta(hours=1)

def get_min_date():
    min_feedback = analyze_data.get_min_from_firebase('date').replace(tzinfo=None)
    min_sensor = analyze_data.get_min_from_mongo('time').replace(tzinfo=None)
    return max(min_feedback, min_sensor)

def get_max_date():
    max_feedback = analyze_data.get_max_from_firebase('date').replace(tzinfo=None)
    max_sensor = analyze_data.get_max_from_mongo('time').replace(tzinfo=None)
    return min(max_feedback, max_sensor)

def get_df_merged_data(**kwargs):
    global df_merged
    if df_merged is None:
        df_merged = merge_data.df_merge_from_file('./all_feedbacks.csv', **kwargs)
    return df_merged

def get_unique_sensor_types():
    return get_df_merged_data()['sensor_type'].unique()

def get_df_sensor():
    global df_merged
    global df_data_last_time
    if not(df_merged) or (datetime.utcnow() - df_data_last_time) > timedelta(hours=1):
        df_merged = get_df_merged_data()
        df_data_last_time = datetime.utcnow()
 
    return df_merged
