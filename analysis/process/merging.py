"""Module for the load & merging of the data from the datasources"""
from typing import List
import copy

import pandas as pd

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg

import analysis.config as cfg

MergeVoteWithMeasuresAvailableFields = ['type', 'subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp', 'sensor', 'sensor_type', 'sensor_id', 'sensor_avg', 'sensor_count', 'sensor_min', 'sensor_max']
    
def _list_votes_with_sensor_data_from_mongo_db(mongo_sensor_collection, feedback_record: dict, group_id_type: mg.GROUP_SENSORS_USING_TYPE) -> List[dict]:
    sensors_in_range_and_room_of_vote = mg.get_average_sensor_data(mongo_sensor_collection,
                                                                   feedback_record['date'],
                                                                   feedback_record['duration'],
                                                                   feedback_record['room'],
                                                                   group_id_type)
    new_records = [{'sensor': sensor['_id'],
                    'sensor_type': sensor['_id']['sensor'],
                    'sensor_id': "-".join(sensor['_id'].values()),
                    'sensor_avg': sensor['avg'],
                    'sensor_count': sensor['count'],
                    'sensor_min': sensor['min'],
                    'sensor_max': sensor['max'],
                    }
                   for sensor in sensors_in_range_and_room_of_vote]

    return new_records

# ** FEEDBACK **

def df_loader_from_file(feedback_file: str, **kwargs) -> pd.DataFrame:
    gen_feedback = fb.generator_feedback_keyvalue_from_csv_file(filename=feedback_file)
    return pd.DataFrame(data=gen_feedback, columns=fb.FlattenVoteFieldsList).astype(fb.get_metadata().dtypes.to_dict())

def compose_firebase_where_filter(firebase_collection, filters):
    filtered_firebase_collection = firebase_collection
    for key, value in filters:
        if key.startsWith('min_'):
            filtered_firebase_collection = filtered_firebase_collection.where(key, '>=', value)
        elif key.startsWith('max_'):
            filtered_firebase_collection = filtered_firebase_collection.where(key, '<=', value)
        else:
            filtered_firebase_collection = filtered_firebase_collection.where(key, '=', value)
    return filtered_firebase_collection

def df_loader_from_firebase(**kwargs) -> pd.DataFrame:
    firebase_collection = fb.get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection)
    stream = compose_firebase_where_filter(firebase_collection, filters=kwargs).stream()
    gen_feedback = fb.generator_flatten_feedback(stream)
    result = pd.DataFrame(data=gen_feedback, columns=fb.FlattenVoteFieldsList).astype(fb.get_metadata().dtypes.to_dict())
    return result

# ** SENSORS **

def compose_mongo_filter(collection, filters):
    if filters:
        return collection.aggregate({'$match': {k: v for k,v in filters.items()}})
    else:
        return collection

def df_loader_from_mongo(**kwargs) -> pd.DataFrame:
    cluster = mg.get_all_sensor_data(mg.get_mongodb_collection())
    filtered_cluster = compose_mongo_filter(cluster, filters=kwargs)
    return pd.DataFrame(data=mg.generator_from_mongo_cursor(filtered_cluster)).astype(mg.get_metadata().dtypes.to_dict())

# ** MERGE **

def create_extended_feedback_df_with_sensor_data(df: pd.DataFrame, group_by: mg.GROUP_SENSORS_USING_TYPE, **kwargs) -> pd.DataFrame:
    """
    Returns a new dataframe with the feedback data and flatten information for each sensor
    """
    rows = []
    for k, row in df.iterrows():
        new_rows = _list_votes_with_sensor_data_from_mongo_db({**row}, group_id_type=group_by)
        rows.extend(new_rows)
    result = pd.DataFrame(rows)
    return result

def add_extended_feedback_df_with_sensor_data(df: pd.DataFrame, group_by: mg.GROUP_SENSORS_USING_TYPE, **kwargs) -> pd.DataFrame:
    """
    Returns a new dataframe with the feedback data and flatten information for each sensor
    """
    df['sensor_info'] = df.apply(lambda x: _list_votes_with_sensor_data_from_mongo_db(sensor_col, {**x}, group_id_type=group_by), axis=1)
    result = df.explode('sensor_info', ignore_index=True)
    return result
    
def df_merge_from_file(filename: str, group_id_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', **kwargs) -> pd.DataFrame:
    """
    Returns a new dataframe with the merging of stored feedback and the sensor data from Mongo.
    """
    df = df_loader_from_file(filename)
    df2 = add_extended_feedback_df_with_sensor_data(copy.deepcopy(df[df['category'] == 'Estado físico']), group_id_type)
    df_extended = df2.drop('sensor_info', axis=1).join(pd.DataFrame(df2.sensor_info.values.tolist()))

    return df_extended
    
def df_merge_from_database(group_id_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', **kwargs) -> pd.DataFrame:
    """
    Returns a new dataframe with the merging of feedback from Firebase and the sensor data from Mongo.
    """
    df = df_loader_from_firebase(**kwargs)
    df2 = add_extended_feedback_df_with_sensor_data(copy.deepcopy(df[df['category'] == 'Estado físico']), group_id_type)
    df_extended = df2.drop('sensor_info', axis=1).join(pd.DataFrame(df2.sensor_info.values.tolist()))

    return df_extended

