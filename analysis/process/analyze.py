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

def get_min_from_df(field, df):
    return df[field].min()

def get_max_from_df(field, df):
    return df[field].max()

def get_uniques_from_df(field, df):
    return df[field].distinct()
