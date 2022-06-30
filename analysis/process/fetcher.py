"""
Retrieves the data needed by the frontend services.
"""
from datetime import date, datetime
from typing import List, Optional

import pandas as pd
from pandas.core.dtypes.cast import astype_dt64_to_dt64tz

import analysis.config as cfg
import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg
import analysis.process.analyze as an


def calculate_sensors(ini_datetime: datetime, end_datetime: datetime, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor'):
    print('calculate_sensors')
    cursor = mg.mongo_sensor_reading(ini_datetime, end_datetime, room=room, sensor_types=cfg.get_sensors_for_measure(measure))
    dfcursor = pd.DataFrame(cursor)
    # from my own:
    dfcursor['new_vals'] = dfcursor.apply(lambda x: [{'sensor':k, 'value': v} for k, v in x['data'].items()], axis=1)
    dfcursor.drop('data', axis=1)
    temp1 = dfcursor.explode('new_vals')
    result = pd.concat([temp1, temp1['new_vals'].apply(pd.Series)], axis=1)
    result.drop('new_vals', axis=1)
    result.dropna(axis=0)
    result['measure'] = result['sensor'].map(cfg.get_measure_from_sensor)
    result.reset_index()
    print('calculate_sensors', type(result), result.shape)
    return result

def calculate_feedback(ini_datetime: datetime, end_datetime: datetime, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor'):
    print('calculate_feedback')
    custom_generator = fb.firebase_feedback_reading(start_date=ini_datetime, end_date=end_datetime, measure=measure, category=category, room=room)
    dfstream = pd.DataFrame(custom_generator)
    temp1 = dfstream.explode('votingTuple')
    result = pd.concat([temp1, temp1['votingTuple'].apply(pd.Series)], axis=1)
    result.drop('votingTuple', axis=1)
    result.dropna(axis=0)
    result['measure'] = result['reasonsList'].map(cfg.get_measure_from_reasons)
    result.reset_index()
    
    print('calculate_feedback')
    return result

    
def filter_data(ddf: pd.DataFrame, measure: str, room_field:str, rooms: str, m_field: str, m_filter: str) -> pd.DataFrame:
    print(f'filter_timeline {ddf.shape=}, {measure=}, {room_field=}, {rooms=}, {m_field=}, {m_filter=}')
    df_filter = (ddf[m_field].str.contains(m_filter))
    if rooms:
        df_filter &= (ddf[room_field] == rooms)
    result = ddf[df_filter]
    print('filter_timeline', type(result), result.shape)
    return result


def build_timeseries(sensor_data: pd.DataFrame, time_field: str, freq: str, field_value: str):
    grouped_by_period = sensor_data.groupby(pd.Grouper(key=time_field, axis=0, freq=freq, sort=True)).agg({field_value: 'mean'}).reset_index()
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

def all_rooms():
    all_rooms = an.get_unique_from_mongo('class')
    return all_rooms

if __name__ == '__main__':
    df = calculate_feedback(datetime(2020,1,1), datetime(2022,7,1), 'Ambiente', None, None)
    print(df.shape)
    print(df.columns)
    print(df)
