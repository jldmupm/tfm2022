from datetime import date, datetime
import logging

from fastapi import Depends

import analysis.config as cfg

import pandas as pd
    
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

# sensor data/timeline

async def get_plain_sensor_data(request: api.models.SensorizationTimelineRequest) -> pd.DataFrame:
    ini_datetime, end_datetime = get_min_max_datetime(request.ini_date, request.end_date)
    df = fetcher.calculate_sensors(ini_datetime, end_datetime, 'Ambiente', measure=request.measure, room=request.room)
    
    return df

async def get_sensor_data(request: api.models.SensorizationTimelineRequest, data=Depends(get_plain_sensor_data)) -> pd.DataFrame:
    filtered = fetcher.filter_data(data, measure=request.measure, filter_error=' (sensor != "error")', room_field='class', rooms=request.room)
    
    return filtered

async def get_sensor_timeline(request: api.models.SensorizationTimelineRequest, data=Depends(get_sensor_data)):
    ini_datetime, end_datetime = get_min_max_datetime(request.ini_date, request.end_date)
    timeline = fetcher.build_timeseries(data, ini_datetime=ini_datetime, end_datetime=end_datetime, time_field='time', freq=request.freq, agg_field_value='value', room_field='class')
    return timeline

# feedback data/timeline

async def get_plain_feedback_data(request: api.models.FeedbackTimelineRequest) -> pd.DataFrame:
    ini_datetime, end_datetime = get_min_max_datetime(request.ini_date, request.end_date)
    df = fetcher.calculate_feedback(ini_datetime, end_datetime, 'Ambiente', measure=request.measure, room=request.room)
    return df

async def get_feedback_data(request: api.models.FeedbackTimelineRequest, data=Depends(get_plain_feedback_data)) -> pd.DataFrame:
    filtered = fetcher.filter_data(data, measure=request.measure, room_field='room', rooms=request.room)
    return filtered

async def get_feedback_timeline(request: api.models.FeedbackTimelineRequest, data=Depends(get_feedback_data)) -> pd.DataFrame:
    ini_datetime, end_datetime = get_min_max_datetime(request.ini_date, request.end_date)
    timeline = fetcher.build_timeseries(data, ini_datetime=ini_datetime, end_datetime=end_datetime, time_field='date', freq=request.freq, agg_field_value='score', room_field='room', fill_value=3.0)
    return timeline


async def get_merged_timeline(df_sensor_data=Depends(get_sensor_timeline),
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
                                     on=['dt', 'room', 'measure']
                                     )
    df_merged_data = df_merged_data.fillna(value=0)
    df_merged_data.reset_index()

    return df_merged_data

async def get_measures_correlation_matrix_with_average(data: pd.DataFrame=Depends(get_sensor_timeline)):
    data = data.reset_index()
    print('='*70)
    print(data)
    if data.empty:
        return data
    measures_as_vars = pd.pivot_table(data, values='value_mean', columns='measure', index=['dt', 'room'])
    print('='*70)
    print(measures_as_vars)
    measures_as_vars.to_csv('./mostrar.csv')
    correlations = measures_as_vars.corr().fillna(value=0)
    print('='*70)
    print(correlations)
    return correlations

async def get_measures_correlation_matrix_with_score(data: pd.DataFrame=Depends(get_merged_timeline)):
    measures_as_vars = pd.pivot_table(data, values='value_mean_vote', columns='measure', index=['dt', 'room'])
    if measures_as_vars.empty:
        return measures_as_vars
    correlations = measures_as_vars.corr().fillna(value=3.0)
    return correlations

async def get_linear_regression(request: api.models.LogisticRegressionParameters, data: pd.DataFrame = Depends(get_merged_timeline)):
    if not data.empty:
        regression = analizer.get_regression(data, test_size=request.test_size)
        print(regression)
    else:
        regression = {}
    return regression
