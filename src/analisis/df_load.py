from typing import List

import pandas as pd
from firebase_admin import firestore

import src.feedback.fs_source as fs

def load_dataframe(filters: List[fs.FirestoreFilterType] = [], sort_by = None, limit: int = None, limit_to_last: int = None) -> pd.DataFrame:
    "Returns a pandas DataFrame from the Firestore"
    df = pd.DataFrame(data=fs.generator_feedback_tuple(filters=filters,
                                                       order_by = sort_by, limit=limit, limit_to_last=limit_to_last),
                      columns=fs.AvailableFieldsList)

    return df

def feedback_min_value(field: str):
    """Return a DocumentRef to the minimun value of the data"""
    client = fs.get_firestore_db_client()
    return next(client.collection("feedback").order_by(field).limit(1).stream())

def feedback_max_value(field: str):
    """Return a DocumentRef to the maximum value of the data"""
    client = fs.get_firestore_db_client()
    return next(client.collection("feedback").order_by(field, direction=firestore.Query.DESCENDING).limit(1).stream())
    
def group_dataframe(df: pd.DataFrame, grouping_date="2H") -> pd.Series:
    res = df.groupby(
        [pd.Grouper(key="date", freq=grouping_date),
         pd.Grouper(key="score"),
         pd.Grouper(key="room"),]
    ).sum()

    return res
