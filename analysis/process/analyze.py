from typing import Callable, List, Optional
from datetime import datetime

import analysis.config as cfg

import numpy as np
import pandas as pd

import modin.pandas as pd

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

def get_regression(df, test_size: float):
    with joblib.parallel_backend('dask'):
        measures_as_vars = pd.pivot_table(df, values='value_mean_sensor', columns='measure', index=['dt', 'room'])
        measures_as_vars.bfill()
        measures_as_vars.sort_index()
        score_as_y = df.groupby(['dt', 'room']).sum().sort_index()
        with_nan1 = df[df.isna().any(axis=1)]
        with_nan2 = measures_as_vars[measures_as_vars.isna().any(axis=1)]
        with_nan3 = score_as_y[score_as_y.isna().any(axis=1)]
        print(with_nan1)
        print('=======================', with_nan1.columns)
        print(with_nan2)
        print('=======================', with_nan2.columns)
        print(with_nan3)
        print('=======================', with_nan3.columns)
        print(measures_as_vars.shape, measures_as_vars)
        print(score_as_y.shape, score_as_y)
        
        x_train, x_test, y_train, y_test = train_test_split(measures_as_vars, score_as_y, test_size=test_size, random_state=42)
        ss_scaler = preprocessing.StandardScaler()
        x_train_ss = ss_scaler.fit_transform(x_train)
        x_test_ss = ss_scaler.transform(x_test)
        lg_model = LogisticRegression()
        lg_model.fit(x_train_ss, y_train)
        y_pred = lg_model.predict(x_test_ss)
        mean_aquracy = lg_model.score(x_test_ss, y_test)
        mse = mean_squared_error(y_test, y_pred)

        coeffs = pd.concat([pd.DataFrame(df.columns),pd.DataFrame(np.transpose(lg_model.coef_))], axis = 1)
        return {
            'aquracy': mean_aquracy,
            'mse': mse,
            'coefficients': coeffs.to_dict(),
            'intercept': lg_model.intercept_
        }
