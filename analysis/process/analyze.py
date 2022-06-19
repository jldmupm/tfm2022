import numpy as np
import pandas as pd
import dask.bag as db
import dask.dataframe as ddf

import analysis.sensors.mg_source as mg
import analysis.feedback.fb_source as fb
import analysis.process.merging as merge

import analysis.config as cfg

def get_metadata():
    meta = pd.DataFrame([], columns=merge.MergeVoteWithMeasuresAvailableFields)
    meta.type = meta.type.astype(str)
    meta.subjectId = meta.subjectId.astype(str)
    meta.date = meta.date.astype(np.datetime64)
    meta.duration = meta.duration.astype(np.unsignedinteger)
    meta.room = meta.room.astype(str)
    meta.reasonsString = meta.reasonsString.astype(str)
    meta.category = meta.category.astype(str)
    meta.score = meta.score.astype(np.number)
    meta.reasonsList = meta.reasonsList.astype(object)
    meta.timestamp = meta.timestamp.astype(np.number)
    meta.sensor = meta.sensor.astype(object)
    meta.sensor_type = meta.sensor.astype(str)
    meta.sensor_id = meta.sensor_id.astype(str)
    meta.sensor_avg = meta.sensor_avg.astype(np.number)
    meta.sensor_count = meta.sensor_count.astype(np.unsignedinteger)
    meta.sensor_min = meta.sensor_min.astype(np.number)
    meta.sensor_max = meta.sensor_max.astype(np.number)

    return meta

def get_sensor_flatten_dask_dataframe(bag: db.Bag) -> ddf.DataFrame:
    return bag.to_dataframe(meta=mg.get_metadata())

def get_feedback_flattend_dask_dataframe(bag: db.Bag) -> ddf.DataFrame:
    d_df = bag.to_dataframe(meta=fb.get_metadata())
    return d_df
    
def get_merged_dask_dataframe(bag: db.Bag) -> ddf.DataFrame:
    d_df: ddf.DataFrame = bag.to_dataframe(meta=get_metadata())
    return d_df

def get_sensor_data(client, **kwargs_filters):
    print('GETTING sensor data')
    global df_data_sensor
    pd.set_option('display.max_columns', None)
    df_data_sensors  = get_sensor_flatten_dask_dataframe(merge.bag_loader_from_mongo(**kwargs_filters))

    res = df_data_sensors
    
    return res

def get_feedback_data(client, **kwargs_filters):
    print('GETTING feedback data')
    global df_data_feedback
    
    pd.set_option('display.max_columns', None)
    df_data_feedback = get_feedback_flattend_dask_dataframe(merge.bag_loader_from_file('./all_feedbacks.csv', **kwargs_filters))

    res = df_data_feedback,

    return res

def get_merged_data(client, **kwargs_filters):
    print('GETTING merged data')
    global df_data_analysis
    
    pd.set_option('display.max_columns', None)
    df_data_analysis = get_merged_dask_dataframe(merge.merge_from_file('./all_feedbacks.csv', **kwargs_filters))

    res = df_data_analysis

    return res

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
    col = mg.get_mongodb_collection(collection).find().sort(field, 1).limit(1)
    ret = next(col)
    return ret[field]
    
def get_max_from_mongo(field, collection=cfg.get_config().datasources.sensors.collection):
    col = mg.get_mongodb_collection(collection).find().sort(field, -1).limit(1)
    ret = next(col)
    return ret[field]

def get_unique_from_mongo(field, collection=cfg.get_config().datasources.sensors.collection):
    lst = mg.get_mongodb_collection(collection).distinct(field)
    return lst

def get_unique_from_bag(field, bag: db.Bag):
    unique_list = bag.distinct(key=field).map(lambda elem: elem.get(field, None)).compute()
    bag.distinct()
    return unique_list
