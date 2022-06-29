"""Module for the load & merging of the data in a Dask Cluster"""
from datetime import date, datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg

import analysis.process.fetcher as fetcher

import analysis.config as cfg


MergeVoteWithMeasuresAvailableFields = ['subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp', 'measure', '_id', 'r_count', 'r_avg', 'r_max', 'r_min', 'r_std', 'sensor_type', 'sensor_id']


def get_metadata() -> pd.DataFrame:
    meta = pd.DataFrame([], columns=MergeVoteWithMeasuresAvailableFields)
#    meta.type = meta.type.astype(str)
    meta.subjectId = meta.subjectId.astype(str)
    meta.date = meta.date.astype(np.datetime64)
    meta.duration = meta.duration.astype(np.unsignedinteger)
    meta.room = meta.room.astype(str)
    meta.reasonsString = meta.reasonsString.astype(str)
    meta.category = meta.category.astype(str)
    meta.score = meta.score.astype(np.number)
    meta.reasonsList = meta.reasonsList.astype(object)
    meta.timestamp = meta.timestamp.astype(np.number)
    meta.measure = meta.measure.astype(str)
    meta._id = meta._id.astype(object)
    meta.r_count = meta.r_count.astype(np.unsignedinteger)
    meta.r_avg = meta.r_avg.astype(np.number)
    meta.r_max = meta.r_max.astype(np.number)
    meta.r_min = meta.r_min.astype(np.number)
    meta.r_std = meta.r_std.astype(np.number)
    meta.sensor_type = meta.sensor_type.astype(object)
    meta.sensor_id = meta.sensor_id.astype(object)
    
    return meta


# ** FEEDBACK **


def df_feedback_loader_from_file(start_timestamp: float, end_timestamp: float, category: str, feedback_file: str) -> DataFrame:
    print('df_feedback_loader_from_file')
    ddf = fb.df_feedback_file_distributed(feedback_file,
                                          start_timestamp=start_timestamp,
                                          end_timestamp=end_timestamp,
                                          category=category)
    print('df_feedback_loader_from_file', type(ddf))
    return ddf
    

def generate_date_portions(ini: datetime, end: datetime, portions=4):
    calc_days=(end - ini).days
    date_list=[ini - timedelta(days=calc_days) for x in range(portions)]
    return date_list, calc_days


def df_feedback_loader_from_firebase(start_timestamp: float, end_timestamp: float, category: str, measure: Optional[str], room: Optional[str]) -> DataFrame:
    print('df_feedback_loader_from_firebase')
    date_ranges, num_days = generate_date_portions(datetime.fromtimestamp(start_timestamp), datetime.fromtimestamp(end_timestamp))
    list_init_timestamps = list(map(lambda d: d.timestamp(), date_ranges))
    
    result = fb.df_firebase_distributed_feedback_vote(
        list_init_timestamps,
        num_days=num_days,
        collection=cfg.get_config().datasources.feedbacks.collection,
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        category=category,
        measure=measure,
        room=room)
    print('df_feedback_loader_from_firebase', type(result))
    return result


# ** SENSORS **


def df_sensors_loader_from_mongo(min_date: datetime, max_date: datetime, measure: Optional[str], room: Optional[str]) -> pd.DataFrame:
    print('df_sensors_loader_from_mongo')
    result = mg.mongo_sensor_reading(min_date, max_date, room=room, sensor_types=cfg.get_sensors_for_measure(measure))
    print('df_sensors_loader_from_mongo', type(result))
    return result

# ** MERGE **

def timeline_feedback(start_date: datetime, end_date: datetime, category: str, measure: str, room: str, timegroup: str):
    print('timeline_feedback')
    loaded_data = fetcher.get_feedback_timeline(start_date.date(), end_date.date(), category=category, measure=measure, room=room)
    filtered_dataframe_feedback = fetcher.filter_timeline(loaded_data, measure=measure, room_field='room', rooms=room, m_field='reasonsString', m_filter="|".join(cfg.get_reasons_for_measure(measure)))
    dataframe_timeline_feedback = filtered_dataframe_feedback.groupby(pd.Grouper(key='date', freq=timegroup)).agg({'score': 'mean'}).reset_index('date')
    print('timeline_feedback', type(dataframe_timeline_feedback))
    return dataframe_timeline_feedback

def timeline_sensors(start_date: datetime, end_date: datetime, category: str, measure: str, room: str, timegroup: str):
    print('timeline_sensors')
    loaded_data = fetcher.get_sensors_timeline(start_date.date(), end_date.date(), category=category, measure=measure, room=room)
    dataframe_sensor = fetcher.filter_timeline(loaded_data['sensors'], measure=measure, room_field='room', rooms=room, m_field='sensor', m_filter="|".join(cfg.get_sensors_for_measure(measure)))
    dataframe_timeline_sensor = dataframe_sensor.groupby(pd.Grouper(key='date', freq=timegroup)).agg({'value': 'mean'}).reset_index('date')
    print('timeline_sensors', type(dataframe_timeline_sensor))
    return dataframe_timeline_sensor

def merge_feedback_sensors(dataframe_timeline_feedback, dataframe_timeline_sensor):
    print('merge_feedback_sensors')
    timeseries = pd.merge_asof(dataframe_timeline_feedback, dataframe_timeline_sensor, on=['date'])
    print('merge_feedback_sensors', type(dataframe_timeline_sensor))
    return timeseries
