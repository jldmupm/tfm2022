"""
Retrieves the data needed by the dashboard.
"""
from datetime import date, datetime
from typing import List

import pandas as pd
import dask.dataframe as dd

import analysis.config as cfg
import analysis.process.dmerge as dm
import analysis.process.analyze as an


def filter_timeline(ddf: dd.DataFrame, measure: str, rooms: List[str]) -> dd.DataFrame:
    print('filter_timeline', measure)
    valid_reasons = "|".join(cfg.get_reasons_for_measure(measure))
    filter = ((ddf['reasonsString'].str.contains(valid_reasons)) & (ddf['room'].isin(rooms)))
    result = ddf[filter]
    return result

def group_timeline(ddf: dd.DataFrame, agg: dict, timegroup: str):
    print(1,ddf.compute().shape)
#    ddf['date'] = pd.to_datetime(ddf['date'])
    print(2,ddf.compute().shape)
    grouper = pd.Grouper(freq=timegroup)
    print(3,ddf.compute().shape)
    ddfg = ddf.map_partitions(lambda df:df.groupby(grouper).agg(agg), meta={'score':float})
    print(4,ddf.compute().shape)
    print(5,ddfg.compute().shape)
    return ddfg

def get_timeline(ini: date, end: date, category: str) -> dd.DataFrame:
    print('get_timeline')
    ini = datetime.combine(ini, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    result = an.calculate_feedback(ini,end,category) # an.calculate_merged_data(ini, end, category)
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
