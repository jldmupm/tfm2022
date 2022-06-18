from datetime import tzinfo
import dask.distributed
import pandas as pd

import analysis.process.analyze as analyze_data

def get_min_date():
    min_feedback = analyze_data.get_min_from_firebase('date').replace(tzinfo=None)
    min_sensor = analyze_data.get_min_from_mongo('time').replace(tzinfo=None)
    return max(min_feedback, min_sensor)

def get_max_date():
    max_feedback = analyze_data.get_max_from_firebase('date').replace(tzinfo=None)
    max_sensor = analyze_data.get_max_from_mongo('time').replace(tzinfo=None)
    return min(max_feedback, max_sensor)

def get_service_distributed_data(client: dask.distributed.Client, **kwargs):
    return analyze_data.get_base_data(client, **kwargs)
