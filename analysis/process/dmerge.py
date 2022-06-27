"""Module for the load & merging of the data in a Dask Cluster"""
from datetime import datetime, timedelta
from typing import List, Optional
import copy

import numpy as np
import pandas as pd
import dask.dataframe as dd
from analysis.api.models import AnalysisCategoriesType

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg

import analysis.config as cfg


MergeVoteWithMeasuresAvailableFields = ['subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp', '_id', 'r_count', 'r_avg', 'r_max', 'r_min', 'r_std', 'sensor_type', 'sensor_id', 'measure']


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
    meta._id = meta._id.astype(object)
    meta.r_count = meta.r_count.astype(np.unsignedinteger)
    meta.r_avg = meta.r_avg.astype(np.number)
    meta.r_max = meta.r_max.astype(np.number)
    meta.r_min = meta.r_min.astype(np.number)
    meta.r_std = meta.r_std.astype(np.number)
    meta.sensor_type = meta.sensor_type.astype(object)
    meta.sensor_id = meta.sensor_id.astype(object)
    meta.measure = meta.measure.astype(str)
    
    return meta


# ** FEEDBACK **


def df_loader_from_file(start_timestamp: float, end_timestamp: float, category: str, feedback_file: str) -> dd.DataFrame:
    print('df_loader_from_file')
    ddf = dd.from_map(fb.df_feedback_file_distributed,[feedback_file], meta=fb.get_metadata(), start_timestamp=start_timestamp, end_timestamp=end_timestamp, category=category)
    return ddf
    

def generate_date_portions(ini: datetime, end: datetime, portions=4):
    calc_days=(end - ini).days
    date_list=[ini - timedelta(days=calc_days) for x in range(portions)]
    return date_list, calc_days


def df_loader_from_firebase(start_timestamp: float, end_timestamp: float, category: str) -> dd.DataFrame:
    print('df_loader_from_firebase')
    date_ranges, num_days = generate_date_portions(datetime.fromtimestamp(start_timestamp), datetime.fromtimestamp(end_timestamp))
    list_init_timestamps = list(map(lambda d: d.timestamp(), date_ranges))
    
    result = dd.from_map(fb.df_feedback_file_distributed,
                         list_init_timestamps,
                         num_days=num_days,
                         collection=cfg.get_config().datasources.feedbacks.collection,
                         meta=fb.get_metadata(),
                         start_timestamp=start_timestamp,
                         end_timestamp=end_timestamp,
                         category=category)
    return result


# ** SENSORS **


def compose_mongo_filter(filters) -> Optional[dict]:
    if filters:
        return {'$match': {k: v for k,v in filters.items()}}
    else:
        return None


def df_loader_from_mongo(**kwargs) -> dd.DataFrame:
    mongo_filters = compose_mongo_filter(filters=kwargs)
    return dd.from_map(mg.mongo_distributed_sensor_reading, [mongo_filters], meta=mg.get_metadata())


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

