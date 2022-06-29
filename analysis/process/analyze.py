from typing import Callable, List, Optional
from datetime import datetime

import numpy as np
import pandas as pd

import analysis.sensors.mg_source as mg
import analysis.feedback.fb_source as fb

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
