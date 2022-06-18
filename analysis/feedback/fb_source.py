# -*- coding: utf-8 -*-
from typing import Generator, List, Tuple
import csv

import dateutil.parser
import firebase_admin
from firebase_admin import firestore
import numpy as np
import pandas as pd

from analysis.config import get_firebase_file_credentials

FlattenVoteFieldsList = ['type', 'id', 'subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp']

FirestoreFilterType = Tuple[str, str, str] # TODO: improve

def get_metadata():
    meta = pd.DataFrame([], columns=FlattenVoteFieldsList)
    meta.type = meta.type.astype(str)
    meta.id = meta.id.astype(str)
    meta.subjectId = meta.subjectId.astype(str)
    meta.date = meta.date.astype(np.datetime64)
    meta.duration = meta.duration.astype(np.unsignedinteger)
    meta.room = meta.room.astype(str)
    meta.reasonsString = meta.reasonsString.astype(str)
    meta.category = meta.category.astype(str)
    meta.score = meta.score.astype(np.number)
    meta.reasonsList = meta.reasonsList.astype(object)
    meta.timestamp = meta.timestamp.astype(np.number)

    return meta

def get_firestore_db_client() -> firebase_admin.App:
    "Get a Firestore Client"
    cred_file = get_firebase_file_credentials()
    cred_obj = firebase_admin.credentials.Certificate(cred_file)
    default_app = firebase_admin.initialize_app(credential=cred_obj)
    firestore_db = firestore.client()
    
    return firestore_db

def generator_feedback_keyvalue_from_csv_file(filename: str) -> Generator[dict, None, None]:
    """Get a generator of 'Key/Value' objects from a CSV file.

    :param filename:
      The filename of a CSV file containing feedback data.
    :returns:
      A generator in which each feedback has been decomposed to each vote.
    """
    with open(filename, 'r') as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
        for feedback in reader:
            feedback['date'] = dateutil.parser.parse(feedback['date']).replace(tzinfo=None)
            # ups! an eval!
            feedback['reasonsList'] = eval(feedback['reasonsList'])
            yield feedback

def flatten_feedback_dict(feedback_dict) -> List[dict]:
    """Convert a Firestore feedback_dict containing survey information to a dictionary of Key/Value pairs.

    :param feedback_dict:
       A dictionary with feedback information.
    :returns:
       A list of dictionaries with one for each category in the feedback.
    """
    lst_dicts = []
    for vote in feedback_dict.get('votingTuple', []):
        new_key_value_dict = {"type": "feeback", **feedback_dict, **vote, "timestamp": feedback_dict['date'].timestamp(), "date": feedback_dict['date'].replace(tzinfo=None)}
        del new_key_value_dict['votingTuple']
        lst_dicts.append(new_key_value_dict)
    if len(feedback_dict.get('votingTuple', [])) == 0:
        lst_dicts = [{"type": "feeback", **feedback_dict, "timestamp": feedback_dict['date'].timestamp()}]
    return lst_dicts
