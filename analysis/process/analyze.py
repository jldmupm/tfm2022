from typing import Callable, List, Optional
from datetime import datetime

import numpy as np
import pandas as pd

import analysis.sensors.mg_source as mg
import analysis.feedback.fb_source as fb
import analysis.process.dmerge as dm

import analysis.config as cfg


def get_min_from_firebase(field, collection=cfg.get_config().datasources.feedbacks.collection):
    col = fb.get_firestore_db_client().collection(collection)
    filter_col = col.order_by(field).limit(1)
    doc_ref = next(filter_col.stream())
    return doc_ref.to_dict()[field]

def get_max_from_firebase(field, collection=cfg.get_config().datasources.feedbacks.collection):
    col = fb.get_firestore_db_client().collection(collection)
    filter_col = col.order_by(field).limit_to_last(1)
    doc_ref = filter_col.get()[0]
    return doc_ref.to_dict()[field]

def get_min_from_mongo(field, collection=cfg.get_config().datasources.sensors.collection):
    col = mg.get_mongodb_collection().find().sort(field, 1).limit(1)
    ret = next(col)
    return ret[field]
    
def get_max_from_mongo(field, collection=cfg.get_config().datasources.sensors.collection):
    col = mg.get_mongodb_collection().find().sort(field, -1).limit(1)
    ret = next(col)
    return ret[field]

def get_unique_from_mongo(field, collection=cfg.get_config().datasources.sensors.collection) -> list:
    print('get_unique_from_mongo', field)
    lst = mg.get_mongodb_collection().distinct(field)
    print('get_unique_from_mongo')
    return [m for m in lst]

def get_min_from_df(field, df):
    return df[field].min()

def get_max_from_df(field, df):
    return df[field].max()

def get_uniques_from_df(field, df):
    return df[field].distinct()

def calculate_feedback(start_at, end_at, category: str, measure: Optional[str], room: Optional[str], group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> pd.DataFrame:
    """
    Serving the feedback data.
    """
    print('calculate_feedbac')
    # check if a file or firestore should be used to retrieve feedback data and load and filter it
    if cfg.fileForFeedback():
        print('From file...')
        ddf = dm.df_feedback_loader_from_file(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category, feedback_file=cfg.fileForFeedback())
    else:
        print('From Firestore...')
        ddf = dm.df_feedback_loader_from_firebase(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category, measure=measure, room=room)
    ddf = ddf.drop(labels=['id', 'type'], axis=1)
    print('calculate_feedback', ddf.columns)
    return ddf


def calculate_sensors(start_at: datetime, end_at: datetime, category: str, measure: Optional[str], room: Optional[str], group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> pd.DataFrame:
    """
    Serving sensors data.
    """
    print('calculate_sensors')
    ddf = dm.df_sensors_loader_from_mongo(min_date=start_at, max_date=end_at, measure=measure, room=room)
    print('calculate_sensors', type(ddf))
    return ddf

def calculate_merged_data(start_at, end_at, category: str, measure: Optional[str] = None, room: Optional[str] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> pd.DataFrame:
    """
    Serving the merged data.
    """
    print('calculate_merged_data')
    def sensor_data_row_average(x, group_type = 'group_kind_type'):
        return mg.get_average_sensor_data(mg.get_mongodb_collection(),
                                          feedback_timestamp=x['timestamp'],
                                          feedback_duration=x['duration'],
                                          feedback_room=x['room'],
                                          group_type=group_type)

    
    # check if a file or firestore should be used to retrieve feedback data and load and filter it
    if cfg.fileForFeedback():
        print('From file...')
        ddf = dm.df_feedback_loader_from_file(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category, feedback_file=cfg.fileForFeedback())
    else:
        print('From Firestore...')
        ddf = dm.df_feedback_loader_from_firebase(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category, measure=measure, room=room)
    ddf = ddf.drop(labels=['id', 'type'], axis=1)
    
    # get the pairs that will be queried from the sensors database.
    groups_to_query = ddf[['timestamp', 'duration', 'room']].drop_duplicates()
    # query and store the sensors data
    groups_to_query['sensor_data'] = groups_to_query.apply(func=sensor_data_row_average, group_type=group_type, axis=1, meta=("sensor_data", "object"))
    # remove rows without sensor data
    groups_to_query = groups_to_query[groups_to_query['sensor_data'].str.len() > 0]
    # apply the queried sensor data to the feeback.
    ddf_merged = pd.merge(left=ddf, right=groups_to_query, how='right', left_on=['timestamp', 'duration', 'room'], right_on=['timestamp', 'duration', 'room'])
    # remove votes without sensor data
    ddf_merged = ddf_merged[ddf_merged['sensor_data'].str.len() > 0]

    ddf_exploded = ddf_merged.explode('sensor_data')
    ddf_exploded['sensor_data'] = ddf_exploded.apply('sensor_data', axis=1, meta=('sensor_data', 'object'))
    ddf_full = ddf_exploded.map_partitions(lambda df: df.drop('sensor_data', axis=1).join(pd.DataFrame(df.sensor_data.values.tolist())), meta=dm.get_metadata())

    return ddf_full


if __name__ == '__main__':
    from datetime import datetime
    dd = calculate_merged_data(start_at=datetime(2021,10,1), end_at=datetime(2023,1,1), category='Ambiente')
    df = pd.head()
    print(df)
