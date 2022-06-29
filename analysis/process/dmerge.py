"""Module for the load & merging of the data in a Dask Cluster"""
from datetime import datetime, timedelta
from typing import Optional

import numpy as np
import pandas as pd
from pandas import DataFrame

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg

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


# def add_extended_feedback_df_with_sensor_data(df: dd.DataFrame, group_by: mg.GROUP_SENSORS_USING_TYPE, **kwargs) -> dd.DataFrame:
#     """
#     Returns a new dataframe with the feedback data and flatten information for each sensor
#     """
#     def distributed_list_votes_with_sensor_data_from_mongo_db(feedback_dict: dict, group_by: mg.GROUP_SENSORS_USING_TYPE):
#         col = mg.get_mongodb_collection()
#         return _list_votes_with_sensor_data_from_mongo_db(col, feedback_dict, group_by)


#     def sensor_info_json_normalize(df: pd.DataFrame) -> pd.DataFrame:
#         df = pd.json_normalize(df['sensor_info'])

#     df['sensor_info'] = df.apply(lambda x: distributed_list_votes_with_sensor_data_from_mongo_db({**x}, group_by), axis=1, meta="object")
#     df_m = df.explode('sensor_info')
#     result = df_m.map_partitions(sensor_info_json_normalize, meta=get_metadata())
#     return result


# def df_merge_from_file(filename: str, group_id_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', categories=["Estado físico"], **kwargs) -> dd.DataFrame:
#     """
#     Returns a new dataframe with the merging of stored feedback and the sensor data from Mongo.
#     """
#     df = df_loader_from_file(feedback_file=filename, start_timestamp=0, end_timestamp=0, category=categories)
#     df2 = add_extended_feedback_df_with_sensor_data(copy.deepcopy(df), group_id_type)
#     df_extended = df2.drop('sensor_info', axis=1).join(pd.DataFrame(df2.sensor_info.values))

#     return df_extended


# def df_merge_from_database(group_id_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', categories="Estado físico", **kwargs) -> dd.DataFrame:
#     """
#     Returns a new dataframe with the merging of feedback from Firebase and the sensor data from Mongo.
#     """
#     df = df_loader_from_firebase(**kwargs)
#     df2 = add_extended_feedback_df_with_sensor_data(copy.deepcopy(df), group_id_type)
#     df_extended = df2.drop('sensor_info', axis=1).join(dd.DataFrame(df2.sensor_info.values.tolist()))

#     return df_extended

