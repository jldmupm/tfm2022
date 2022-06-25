"""
Retrieves the data needed by the dashboard.
"""
from datetime import date, datetime
from typing import List, Optional

import pandas as pd

import analysis.config as cfg
import analysis.process.analyze as an

def filter_timeline(ddf: pd.DataFrame, measure: str, room_field:str, rooms: str, m_field: str, m_filter: str) -> pd.DataFrame:
    print('filter_timeline')
    filter = ((ddf[m_field].str.contains(m_filter)) & (ddf[room_field] == rooms))
    result = ddf[filter]
    print('filter_timeline', type(ddf))
    return result

def group_timeline(ddf: pd.DataFrame, agg: dict, timegroup: str, meta: dict) -> pd.DataFrame:
    print('group_timeline')
    grouper = pd.Grouper(freq=timegroup)
    ddfg = ddf.map_partitions(lambda df:df.groupby(grouper).agg(agg), meta=meta)
    print('group_timeline', type(ddfg))
    return ddfg

def get_feedback_timeline(ini: date, end: date, category: str, measure: Optional[str]=None, room: Optional[str]=None) -> pd.DataFrame:
    print('get_feedback_timeline')
    ini = datetime.combine(ini, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    result = an.calculate_feedback(ini, end, category, measure, room) # an.calculate_merged_data(ini, end, category)
    print('get_feedback_timeline', result.columns)
    return result

def get_sensors_timeline(ini: date, end: date, category: str, measure: Optional[str] = None, room: Optional[str] = None) -> pd.DataFrame:
    print('get_sensors_timeline')
    ini_datetime = datetime.combine(ini, datetime.min.time())
    end_datetime = datetime.combine(end, datetime.min.time())
    result = an.calculate_sensors(ini_datetime, end_datetime, category, measure, room) # an.calculate_merged_data(ini, end, category)
    print('get_sensors_timeline', type(result))
    return result

def all_measures():
    return [item for item in cfg.get_config().data.sensors.keys()]

def reasons_for_sensor(sensor: str) -> dict:
    return cfg.get_config().data.feedback.sense[sensor]

def sensor_type_for_sensor(sensor: str) -> List[str]:
    return cfg.get_config().data.sensors[sensor]

def all_rooms():
    all_rooms = an.get_unique_from_mongo('class')
    return all_rooms
