"""
Retrieves the data needed by the frontend services.
"""
from datetime import date, datetime
from typing import List, Optional
import logging

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
                    'measure': 'object'
                    }
sensor_raw_columns = {
    '_id': 'object',
    'time': 'object',
    'data': 'object',
    'class': 'object',
    'hub': 'object',
    'node': 'object',
    'id': 'object',
}

sensor_end_columns = {
    '_id': 'object',
    'time': 'object',
    'data': 'object',
    'class': 'object',
    'hub': 'object',
    'node': 'object',
    'id': 'object',
    'measure': 'object',
    'sensor': 'object',
    'value': 'float',
}


# TODO: distributed calculate feedback & sensors: read from a single day and concat results.

@cachier(mongetter=cache_app_mongetter)
def calculate_sensors(ini_datetime: datetime, end_datetime: datetime, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> DataFrame:    
    cursor = mg.mongo_sensor_reading(ini_datetime, end_datetime, room=room, sensor_types=cfg.get_sensors_for_measure(measure))
    dfcursor = pd.DataFrame(cursor)#, columns=sensor_raw_columns.keys())
    
    # from my own:
    if dfcursor.empty:
        return pd.DataFrame({k: [] for k in sensor_end_columns.keys()})
    dfcursor['new_vals'] = dfcursor.apply(lambda x: [{'sensor':k, 'value': v} for k, v in x['data'].items()], axis=1)
    temp1 = dfcursor.explode('new_vals')
    result = pd.concat([temp1, temp1['new_vals'].apply(pd.Series)], axis=1)
    
    result.drop(columns=['new_vals', 'data'], axis=1, inplace=True)
    result.dropna(axis=0)
    
    result.reset_index()
    
    result['measure'] = result.apply(lambda row: cfg.get_measure_from_sensor(row['sensor']), axis=1)

    return result

#@cachier(mongetter=cache_app_mongetter)
def calculate_feedback(ini_datetime: datetime, end_datetime: datetime, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> DataFrame:
    
    custom_generator = fb.firebase_feedback_reading(start_date=ini_datetime, end_date=end_datetime, measure=measure, category=category, room=room)
    dfstream = pd.DataFrame(custom_generator)
    if dfstream.empty:
        return pd.DataFrame({k: [] for k in feedback_columns.keys()})
    if room is not None:
        dfstream = dfstream[dfstream['room'] == room]
    if dfstream.empty:
        return pd.DataFrame({k: [] for k in feedback_columns.keys()})
    temp1 = dfstream.explode('votingTuple')
    result = pd.concat([temp1, temp1['votingTuple'].apply(pd.Series)], axis=1)
    result.drop('votingTuple', axis=1, inplace=True)
    result.dropna(axis=0)
    
    result['measure'] = result['reasonsList'].map(cfg.get_measure_from_reasons)

    if measure is not None:
        result = result[result['measure'] == measure]
    result.reset_index()
    
    
    return result


def filter_data(ddf: pd.DataFrame, measure: Optional[str] = None, room_field: Optional[str] = None, rooms: Optional[str] = None, field: Optional[str] = None, value: Optional[str] = None, filter_error: Optional[str] = None) -> DataFrame:
    
    query_params = { }
    if field and value:
        query_params = {**query_params, field: value}
    if room_field and rooms:
        query_params = {**query_params, room_field: rooms}
    if measure:
        query_params = {**query_params, 'measure': measure}
    query_rest = ' & '.join([' (`{}` == "{}") '.format(k, v) for k, v in query_params.items()])
    # filter out errors
    query = query_rest
    if (len(query_rest) > 0) and filter_error and (len(filter_error) > 0):
        query += ' & '
    if filter_error and (len(filter_error) > 0):
        query += filter_error
    logging.debug(f"filter_data: {type(ddf)=},{ddf.columns=},{query=}")
    if len(query) > 0:
        result = ddf.query(query)
    else:
        result = ddf
        
    return result


def build_timeseries(data: pd.DataFrame, time_field: str, freq: str, agg_field_value: str, room_field: Optional[str]) -> DataFrame:
    data['dt'] = pd.to_datetime(data.loc[:,time_field])
    aggregations = {agg_field_value + '_' + v: ( agg_field_value, v ) for v in ['min', 'mean', 'max', 'std', 'count']}
    grouped_by_period = data.groupby([pd.Grouper(key='dt', axis=0, freq=freq, sort=True), pd.Grouper(key='measure'), pd.Grouper(key=room_field)]).agg(**aggregations).apply(lambda x: x.fillna(x.mean())).reset_index()
    return grouped_by_period


def all_measures():
    return [item for item in cfg.get_config().data.sensors.keys()]

def reasons_for_sensor(sensor: str) -> dict:
    return cfg.get_config().data.feedback.sense[sensor]


def sensor_type_for_sensor(sensor: str) -> List[str]:
    return cfg.get_config().data.sensors[sensor]


def sensorized_rooms():
    sensor_rooms = an.get_unique_from_mongo('class')

    return sensor_rooms

def feedback_rooms():
    feedback_rooms = [room for room in fb.get_rooms() if room]
    return feedback_rooms
