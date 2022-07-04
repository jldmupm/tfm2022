"""
Retrieves the data needed by the frontend services.
"""
from datetime import date, datetime
from typing import List, Optional

import analysis.config as cfg

import pandas as pd
if cfg.get_config().cluster.scheduler_type in ['distributed']:
    import modin.pandas as pd
from pandas import DataFrame

from cachier import cachier
from analysis.cache import cache_app_mongetter

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg
import analysis.process.analyze as an

feedback_columns = {'subjectId': 'object',
                    'duration': 'int16',
                    'room': 'object',
                    'date': 'object',
                    'reasonsString': 'object',
                    'score': 'int16',
                    'reasonsList': 'object',
                    'category': 'object',
                    'measure': 'object'}
sensor_columns = {
    '_id': 'object',
    'time': 'object',
    'data': 'object',
    'class': 'object',
    'hub': 'object',
    'node': 'object',
    'id': 'object',
}

# TODO: distributed calculate feedback & sensors: read from a single day and concat results.

#@cachier(mongetter=cache_app_mongetter)
def calculate_sensors(ini_datetime: datetime, end_datetime: datetime, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> DataFrame:
    print('calculate_sensors')
    cursor = mg.mongo_sensor_reading(ini_datetime, end_datetime, room=room, sensor_types=cfg.get_sensors_for_measure(measure))
    dfcursor = pd.DataFrame(cursor, columns=sensor_columns.keys())
    # from my own:
    if dfcursor.empty:
        return pd.DataFrame({k: [] for k in sensor_columns.keys()})
    dfcursor['new_vals'] = dfcursor.apply(lambda x: [{'sensor':k, 'value': v} for k, v in x['data'].items()], axis=1)
    temp1 = dfcursor.explode('new_vals')
    result = pd.concat([temp1, temp1['new_vals'].apply(pd.Series)], axis=1)
    print('calculate_sensors', type(result), result.shape, result.columns)
    result.drop(columns=['new_vals', 'data'], axis=1, inplace=True)
    result.dropna(axis=0)
    print('calculate_sensors', type(result), result.shape, result.columns, print(type(result['sensor'])))
    result['measure'] = result['sensor'].map(cfg.get_measure_from_sensor)
    result.reset_index()
    print('calculate_sensors', type(result), result.shape, result.columns)
    return result

#@cachier(mongetter=cache_app_mongetter)
def calculate_feedback(ini_datetime: datetime, end_datetime: datetime, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> DataFrame:
    print('calculate_feedback')
    custom_generator = fb.firebase_feedback_reading(start_date=ini_datetime, end_date=end_datetime, measure=measure, category=category, room=room)
    dfstream = pd.DataFrame(custom_generator)
    if dfstream.empty:
        return pd.DataFrame({k: [] for k in feedback_columns.keys()})
    if room is not None:
        dfstream = dfstream[dfstream['room'] == room]
    temp1 = dfstream.explode('votingTuple')
    result = pd.concat([temp1, temp1['votingTuple'].apply(pd.Series)], axis=1)
    result.drop('votingTuple', axis=1, inplace=True)
    result.dropna(axis=0)
    print('before_map', type(result), result.shape, result.columns)
    result['measure'] = result['reasonsList'].map(cfg.get_measure_from_reasons)
    print('after_map', type(result), result.shape, result.columns)
    if measure is not None:
        result = result[result['measure'] == measure]
    result.reset_index()
    
    print('calculate_feedback')
    return result


def filter_data(ddf: pd.DataFrame, measure: str, room_field: Optional[str] = None, rooms: Optional[str] = None, field: Optional[str] = None, value: Optional[str] = None) -> DataFrame:
    df_filter = True
    if measure:
        df_filter = ddf['measure'] == measure
    if room_field and rooms:
        df_filter &= (ddf[room_field] == rooms)
    if field and value:
        df_filter &= (ddf[field] == value)
        
    result = ddf[df_filter]
    print('filter_timeline', type(result), result.shape)
    return result


def build_timeseries(data: pd.DataFrame, time_field: str, freq: str, agg_field_value: str) -> DataFrame:
    data['dt'] = pd.to_datetime(data.loc[:,time_field])
    aggregations = {agg_field_value + '_' + v: ( agg_field_value, v ) for v in ['min', 'mean', 'max', 'std', 'count']}
    grouped_by_period = data.groupby(pd.Grouper(key='dt', axis=0, freq=freq, sort=True)).agg(**aggregations).apply(lambda x: x.fillna(x.mean())).reset_index()
    return grouped_by_period


# def get_feedback_timeline(ini: date, end: date, category: str, measure: Optional[str]=None, room: Optional[str]=None) -> pd.DataFrame:
#     print('get_feedback_timeline')
#     ini = datetime.combine(ini, datetime.min.time())
#     end = datetime.combine(end, datetime.min.time())
#     result = an.calculate_feedback(ini, end, category, measure, room)
#     print('get_feedback_timeline', result.columns)
#     return result

# def get_sensors_data(ini: date, end: date, category: str, measure: Optional[str] = None, room: Optional[str] = None, timegroup: str = "1D") -> pd.DataFrame:
#     print('get_sensors_data')
#     ini_datetime = datetime.combine(ini, datetime.min.time())
#     end_datetime = datetime.combine(end, datetime.min.time())
#     all_sensor_data = calculate_sensors(ini_datetime, end_datetime, category, measure, room)
    
#     print('get_sensors_data', type(all_sensor_data), all_sensor_data.shape)
#     return all_sensor_data

def all_measures():
    return [item for item in cfg.get_config().data.sensors.keys()]


def reasons_for_sensor(sensor: str) -> dict:
    return cfg.get_config().data.feedback.sense[sensor]


def sensor_type_for_sensor(sensor: str) -> List[str]:
    return cfg.get_config().data.sensors[sensor]


def sensorized_rooms():
    sensor_rooms = an.get_unique_from_mongo('class')
    print(sensor_rooms)
    return sensor_rooms

def feedback_rooms():
    feedback_rooms = [room for room in fb.get_rooms() if room]
    return feedback_rooms
