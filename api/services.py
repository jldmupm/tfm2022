from datetime import date, datetime
import logging

from fastapi import Depends

import analysis.config as cfg

import pandas as pd
if cfg.get_config().cluster.scheduler_type in ['distributed']:
    import modin.pandas as pd
    
import api.models

import analysis.process.fetcher as fetcher


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
    logging.debug(f"get_sensor_data {type(data)=}, {data.shape=}, {data.columns=}")
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
    timeline = fetcher.build_timeseries(data, ini_datetime=ini_datetime, end_datetime=end_datetime, time_field='date', freq=request.freq, agg_field_value='score', room_field='room')
    print(timeline)
    return timeline
