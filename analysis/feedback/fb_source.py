# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from typing import Generator, List, Optional, Tuple
import csv
import uuid

import dateutil.parser
from distributed.worker import get_worker
import firebase_admin
import firebase_admin.firestore as firestore
import numpy as np
import pandas as pd

import analysis.config as cfg

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

firebase_client = None

def get_firestore_db_client() -> firebase_admin.App:
    "Get a Firestore Client"
    global firebase_client
    if firebase_client is None:
        cred_file = cfg.get_firebase_file_credentials()
        cred_obj = firebase_admin.credentials.Certificate(cred_file)
        default_app = firebase_admin.initialize_app(credential=cred_obj, name=str(uuid.uuid4()))
        firestore_db = firestore.client(default_app)
        firebase_client = firestore_db
        
    return firebase_client

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

def gen_feedback_file_distributed(x):
    return pd.DataFrame(data=generator_feedback_keyvalue_from_csv_file(x))

def firebase_distributed_feedback_vote(x, num_days: int, collection: str, start_timestamp:int, end_timestamp:int, category: str):
    print(x,num_days)
    def flatten_feedback_dict(feedback_dict) -> List[dict]:
        i = 0
        lst_dicts = []
        for vote in feedback_dict.get('votingTuple', []):
            new_key_value_dict = {"type": "feeback",
                                  "id":i,
                                  "subjectId": feedback_dict['subjectId'],
                                  "date": feedback_dict['date'].replace(tzinfo=None),
                                  "duration": feedback_dict['duration'],
                                  "room": feedback_dict['room'],
                                  "reasonsString": vote['reasonsString'],
                                  "category": vote['category'],
                                  "score": vote['score'],
                                  "reasonsList": vote['reasonsList'],
                                  "timestamp": feedback_dict['date'].timestamp(),
                                  }
            lst_dicts.append(new_key_value_dict)
            i += i + 1
        return lst_dicts

    def generator_flatten_feedback(docref_stream, **kwargs):
        for doc_ref in docref_stream:
            for vote in flatten_feedback_dict(doc_ref.to_dict()):
                yield vote

    print(datetime.fromtimestamp(start_timestamp))
    print(datetime.fromtimestamp(end_timestamp))
    print(category)
    final_timestamp = (datetime.fromtimestamp(x) + timedelta(num_days)).timestamp()
    firebase_collection = get_firestore_db_client().collection(collection).where('timestamp','>=',x).where('timestamp','<',final_timestamp).stream()
    gen_feedback = generator_flatten_feedback(firebase_collection)

    return pd.DataFrame(data=gen_feedback)
