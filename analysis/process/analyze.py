import json
from typing import Callable, List, Optional
from datetime import datetime

import analysis.config as cfg

import numpy as np
import pandas as pd

from sklearn import preprocessing
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import mean_squared_error
import joblib

import analysis.sensors.mg_source as mg
import analysis.feedback.fb_source as fb


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
    
    lst = mg.get_mongodb_collection().distinct(field)
    
    return [m for m in lst]

def get_min_from_df(field, df):
    return df[field].min()

def get_max_from_df(field, df):
    return df[field].max()

def get_uniques_from_df(field, df):
    return df[field].distinct()

def get_regression(df, test_size: float, C: float = 1e30, penalty: str = 'l2', l1_ratio: float = 0, max_iter=1000):
    df.reset_index()
    
    measures_as_vars = pd.pivot_table(df, values='value_mean_sensor', columns='measure', index=['dt', 'room'])
    measures_as_vars = measures_as_vars.fillna(value=0)
    measures_as_vars.sort_index()

    score_as_y = pd.pivot_table(df, values="value_mean_vote", columns="measure", index=['dt', 'room'])
    score_as_y = score_as_y.fillna(value=3.0)
    score_as_y = score_as_y.round(decimals=0).astype(int) # discrete values
    score_as_y.sort_index()

    x_train, x_test, y_train, y_test = train_test_split(measures_as_vars, score_as_y, test_size=test_size, random_state=42, shuffle=True)
    
    ss_scaler = preprocessing.StandardScaler()
    x_train_ss = ss_scaler.fit_transform(x_train)
    x_test_ss = ss_scaler.transform(x_test)

    frames = {}
    errors = {}
    for measure in score_as_y.columns:
        y_train_measure = y_train[measure]
        y_test_measure = y_test[measure]
        lg_model = LogisticRegression(penalty=penalty, C=C, l1_ratio=l1_ratio, max_iter=max_iter)
        try:
            lg_model.fit(x_train_ss, y_train_measure)
        except Exception as e:
            errors[measure] = str(e)
            continue
    
        y_pred_measure = lg_model.predict(x_test_ss)
        mean_accuracy = lg_model.score(x_test_ss, y_test_measure)
        mse = mean_squared_error(y_test_measure, y_pred_measure)
        
        frames[measure] = {
            'accuracy': mean_accuracy,
            'mse': mse,
            'model': logistic_regression_to_json(lg_model)
        }

    return { 'models': frames, 'errors': errors }


def logistic_regression_to_json(lrmodel, file=None):
    data = {}
    data['init_params'] = lrmodel.get_params()
    data['model_params'] = mp = {}
    for p in ('coef_', 'intercept_','classes_', 'n_iter_'):
        mp[p] = getattr(lrmodel, p).tolist()
    return data

def logistic_regression_from_json(data: dict):
    model = LogisticRegression(**data['init_params'])
    for name, p in data['model_params'].items():
        setattr(model, name, np.array(p))
    return model
