from typing import List
from copy import deepcopy
from datetime import datetime

from fastapi import Depends

import analysis.config as cfg

import pandas as pd
if cfg.get_config().cluster.scheduler_type in ['distributed']:
    import modin.pandas as pd
    
import api.models

import analysis.process.fetcher as fetcher

async def get_plain_feedback_data(request: api.models.FeedbackDataRequest) -> pd.DataFrame:
#    async with Client(cfg.get_cluster(), asynchronous=True) as client:
    ini_datetime = datetime.combine(request.ini_date, datetime.min.time())
    end_datetime = datetime.combine(request.end_date, datetime.max.time())
    df = fetcher.calculate_feedback(ini_datetime, end_datetime, 'Ambiente')
    return df

async def get_feedback_data(request: api.models.FeedbackDataRequest, data=Depends(get_plain_feedback_data)) -> pd.DataFrame:
    print('get_feedback_data data', data.shape, data.columns)
    filtered = fetcher.filter_data(data, measure=request.measure)
    print('get_feedback_data filtered', filtered.shape, filtered.columns)
    return filtered

async def get_feedback_timeline(request: api.models.FeedbackTimelineRequest, data=Depends(get_feedback_data)) -> pd.DataFrame:
    timeline = fetcher.build_timeseries(data, time_field='date', freq=request.freq, agg_field_value='score')
    return timeline

async def get_rooms(from_feedback=Depends(fetcher.feedback_rooms),
                    from_sensors=Depends(fetcher.sensorized_rooms)) -> dict:
    return {'rooms':  from_feedback + from_sensors}

async def get_measures(result=Depends(cfg.get_all_measures)) -> dict:
    return {'measures': result}

async def get_plain_sensor_data(request: api.models.SensorizationDataRequest) -> pd.DataFrame:
    print('get_plain_sensor_data')
    ini_datetime = datetime.combine(request.ini_date, datetime.min.time())
    end_datetime = datetime.combine(request.end_date, datetime.max.time())
    df = fetcher.calculate_sensors(ini_datetime, end_datetime, 'Ambiente')
    print('get_plain_sensor_data', type(df), df.shape)
    return df

async def get_sensor_data(request: api.models.SensorizationDataRequest, data=Depends(get_plain_sensor_data)) -> pd.DataFrame:
    print('get_sensor_data')
    filtered = fetcher.filter_data(data, request.measure, filter_error=' sensor != "error"')
    print('get_sensor_data', type(filtered), filtered.shape, filtered.columns)
    return filtered

async def get_sensor_timeline(request: api.models.FeedbackTimelineRequest, data=Depends(get_sensor_data)):
    print('get_sensor_timeline')
    timeline = fetcher.build_timeseries(data, time_field='time', freq=request.freq, agg_field_value='value')
    return timeline

# def serve_correlations(period: api.models.AnalysisPeriodType, category: api.models.AnalysisCategoriesType, group_type: mg.GROUP_SENSORS_USING_TYPE):
#     """
#     Serving the analysis.
#     """
#     # calculate the period
#     (start_at, end_at) = period.get_period()

    # merged = calculate_merged_data(start_at, end_at, category, group_type)
    # # get all category values
    # [posc, negc] = fb_api.models.CategoriesEnum.AMBIENTE.all_categories()
    # # get all sensor types:
    # sensors_query = merged[['sensor_type']].drop_duplicates()['sensor_type'].compute().tolist()

    # correlations = []
    # for sensor in sensors_query:

    #     for cat in posc:
            
    # list(map(lambda s: {'sensor_type': s, 'correlations': merged[merged['sensor_type'] == s][['score','r_avg']].corr().compute().to_dict()}, sensors_query))


    # result = list(map(lambda e: {'sensor_type': e['sensor_type'], 'correlation_score_avg': e['correlations']['score']['r_avg']}, correlations))
    
    # return {
    #     'start': start_at,
    #     'end': end_at,
    #     'correlations': result
    # }
#    pass
