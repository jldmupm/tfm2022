import dask.distributed

import analysis.sensors.mg_source as mg
import analysis.process.analyze as analyze_data

def get_min_date():
    min_feedback = analyze_data.get_min_from_firebase('date').replace(tzinfo=None)
    min_sensor = analyze_data.get_min_from_mongo('time').replace(tzinfo=None)
    return max(min_feedback, min_sensor)

def get_max_date():
    max_feedback = analyze_data.get_max_from_firebase('date').replace(tzinfo=None)
    max_sensor = analyze_data.get_max_from_mongo('time').replace(tzinfo=None)
    return min(max_feedback, max_sensor)

def get_df_merged_data(client: dask.distributed.Client, **kwargs):
    return analyze_data.get_merged_data(client, **kwargs)

def get_df_feedback_data(client: dask.distributed.Client, **kwargs):
    return analyze_data.get_feedback_data(client, **kwargs)

def get_df_sensor_data(client: dask.distributed.Client, **kwargs):
    return analyze_data.get_sensor_data(client, **kwargs)
