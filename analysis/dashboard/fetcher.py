"""
Retrieves the data needed by the dashboard.
"""
from datetime import date, datetime
from typing import List

import dask.dataframe as dd

import analysis.config as cfg
import analysis.process.analyze as an


def filter_timeline(merged: dd.DataFrame, measure: str, rooms: List[str]) -> dd.DataFrame:
    print('filter_timeline')
    valid_sensors_for_measure = cfg.get_config().data.sensors[measure]
    valid_reasons_for_measure = cfg.get_config().data.feedback.sense[measure]
    plain_valid_reasons_for_measure = valid_reasons_for_measure['pos'] + valid_reasons_for_measure['neg']
    merged_sensor = merged[(merged['sensor_type'].str.contains("|".join(valid_sensors_for_measure))) &
                           (merged['reasonsString'].str.contains("|".join(plain_valid_reasons_for_measure)))]

    result = merged_sensor[merged_sensor['room'].str.contains("|".join(rooms))]
    print('ft',type(result), len(result))
    return result


def get_timeline(ini: date, end: date) -> dd.DataFrame:
    print('get_timeline')
    ini = datetime.combine(ini, datetime.min.time())
    end = datetime.combine(end, datetime.min.time())
    result = an.calculate_merged_data(ini, end)
    print('gt',type(result), len(result))
    return result

def all_sensors():
    return [item for item in cfg.get_config().data.sensors.keys()]

def reasons_for_sensor(sensor: str) -> dict:
    return cfg.get_config().data.feedback.sense[sensor]

def sensor_type_for_sensor(sensor: str) -> List[str]:
    return cfg.get_config().data.sensors[sensor]

def all_rooms():
    all_rooms = an.get_unique_from_mongo('class')
    return all_rooms
