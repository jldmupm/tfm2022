from datetime import date, datetime
from typing import Optional

from fastapi import Depends
import joblib

import analysis.config as cfg

import pandas as pd

from cachier import cachier

from analysis.cache import cache_app_mongetter

import api.models

import analysis.process.fetcher as fetcher
import analysis.process.analyze as analizer

empty_single_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min':[], 'value_mean':[], 'value_max':[], 'value_std':[], 'value_count':[]}
empty_merged_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min_sensor':[], 'value_mean_sensor':[], 'value_max_sensor':[], 'value_std_sensor':[], 'value_count_sensor':[], 'value_min_vote':[], 'value_mean_vote':[], 'value_max_vote':[], 'value_std_vote':[], 'value_count_vote':[]}


def get_min_max_datetime(ini: date, end: date):
    ini_sure = min(ini, end)
    end_sure = max(ini, end)
    ini_datetime = datetime.combine(ini_sure, datetime.min.time())
    end_datetime = datetime.combine(end_sure, datetime.max.time())
    return ini_datetime, end_datetime

async def get_rooms(from_feedback=Depends(fetcher.feedback_rooms),
                    from_sensors=Depends(fetcher.sensorized_rooms)) -> dict:
    return {'rooms':  from_feedback + from_sensors}

async def get_measures(result=Depends(cfg.get_all_measures)) -> dict:
    return {'measures': result}

def hash_dataframe_dependecies(*args, **kwargs):
    hashses = tuple([joblib.hash(arg) for arg in args if isinstance(arg, pd.DataFrame)])
    return hash(hashses)

# sensor data/timeline

@cachier(mongetter=cache_app_mongetter)
def get_sensor_timeline_from_data(ini_datetime: datetime, end_datetime: datetime, category:str='Ambiente', measure:Optional[str]=None, room:Optional[str]=None, freq: str="1D") -> pd.DataFrame:
    print('get_sensor_timeline_from_data', ini_datetime, end_datetime)
    ini_datetime, end_datetime = get_min_max_datetime(ini_datetime, end_datetime)
    print('get_sensor_timeline_from_data (2)', ini_datetime, end_datetime)
    df = fetcher.calculate_sensors(ini_datetime, end_datetime, 'Ambiente', measure=measure, room=room)
    print(df['time'].unique())
    filtered = fetcher.filter_data(df, measure=measure, filter_error=' (sensor != "error")', room_field='class', rooms=room)
    timeline = fetcher.build_timeseries(filtered, ini_datetime=ini_datetime, end_datetime=end_datetime, time_field='time', freq=freq, agg_field_value='value', room_field='class')
    return timeline

def get_sensor_timeline(request: api.models.SensorizationTimelineRequest):
    ini_datetime, end_datetime = get_min_max_datetime(request.ini_date, request.end_date)
    timeline = get_sensor_timeline_from_data(ini_datetime, end_datetime, category='Ambiente', measure=request.measure, room=request.room, freq=request.freq)
    return timeline

# feedback data/timeline

@cachier(mongetter=cache_app_mongetter)
def get_feedback_timeline_from_data(ini_datetime: datetime, end_datetime: datetime, category:str='Ambiente', measure:Optional[str]=None, room:Optional[str]=None, freq: str="1D") -> pd.DataFrame:
    print('get_feedback_timeline_from_data', ini_datetime, end_datetime)
    df = fetcher.calculate_feedback(ini_datetime, end_datetime, category='Ambiente', measure=measure, room=room)
    filtered = fetcher.filter_data(df, measure=measure, room_field='room', rooms=room)
    timeline = fetcher.build_timeseries(filtered, ini_datetime=ini_datetime, end_datetime=end_datetime, time_field='date', freq=freq, agg_field_value='score', room_field='room', fill_value=3.0)
    return timeline

def get_feedback_timeline(request: api.models.FeedbackTimelineRequest) -> pd.DataFrame:
    print('get_feedback_timeline', request.ini_date, request.end_date)
    ini_datetime, end_datetime = get_min_max_datetime(request.ini_date, request.end_date)
    print('get_feedback_timeline (2)', ini_datetime, end_datetime)
    timeline = get_feedback_timeline_from_data(ini_datetime, end_datetime, category='Ambiente', measure=request.measure, room=request.room, freq=request.freq)
                          
    return timeline

def get_merged_timeline(df_sensor_data=Depends(get_sensor_timeline),
                        df_feedback_data=Depends(get_feedback_timeline)
):
    if not df_sensor_data.empty:
        df_sensor = df_sensor_data.reset_index()
    else:
        df_sensor = pd.DataFrame(empty_single_data_set)
    if not df_feedback_data.empty:
        df_feedback = df_feedback_data.reset_index()
    else:
        df_feedback = pd.DataFrame(empty_single_data_set)
    df_merged_data = df_sensor.merge(df_feedback,
                                     how='outer',
                                     suffixes=("_sensor", "_vote"),
                                     on=['dt', 'room', 'measure'])
    
    df_merged_data.fillna({'value_mean_sensor': 0, 'value_std_sensor': 0,
                           'value_max_sensor': 0, 'value_min_sensor': 0,
                           'value_count_sensor':0, 'value_mean_vote': 3, 'value_std_vote': 3,
                           'value_max_vote':3, 'value_min_vote':3, 'value_count_vote':3}, inplace=True)
    df_merged_data.reset_index()
    
    return df_merged_data

async def get_measures_correlation_matrix_with_average(data: pd.DataFrame=Depends(get_sensor_timeline)):
    data = data.reset_index()
    if data.empty:
        return data
    measures_as_vars = pd.pivot_table(data, values='value_mean', columns='measure', index=['dt', 'room'])
    measures_as_vars.to_csv('./mostrar.csv')
    correlations = measures_as_vars.corr().fillna(value=0)
    return correlations

async def get_linear_regression(request: api.models.LogisticRegressionParameters, data: pd.DataFrame = Depends(get_merged_timeline)):
    if not data.empty:
        regression = analizer.get_regression(data, test_size=request.test_size)
    else:
        regression = {'models': {}, 'errors': { 'all': 'empty dataset' } }
    return regression
