# -*- coding: utf-8 -*-
from datetime import datetime
from typing import Generator, List, Tuple, Optional
import csv
import uuid

import analysis.config as cfg

import firebase_admin
import firebase_admin.firestore as firestore

import numpy as np
import pandas as pd


FlattenVoteFieldsList = ['type', 'id', 'subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp', 'measure']

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
    meta.measure = meta.measure.astype(str)
    
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
    i = 0
    with open(filename, 'r') as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
        for feedback in reader:
            # feedback['date'] = dateutil.parser.parse(feedback['date']).replace(tzinfo=None)
            # ups! an eval!
            feedback['reasonsList'] = eval(feedback['reasonsList'])
#            if i<10:
            yield feedback
#            i += 1


def generator_feedback_keyvalue_from_firebase(collection: str, start_timestamp:float, end_timestamp:float, category: str = cfg.get_config().data.feedback.category):
    
    def generator_flatten_feedback(docref_stream, category=[]):
        for doc_ref in docref_stream:
            doc_dict = doc_ref.to_dict()
            for vote in flatten_feedback_dict(doc_dict, category=category):
                yield vote

    ini = datetime.fromtimestamp(start_timestamp)
    final = datetime.fromtimestamp(end_timestamp)
    firebase_collection = get_firestore_db_client().collection(collection).where('date','>=',ini).where('date','<',final)
    gen_feedback = generator_flatten_feedback(firebase_collection.stream(), category=category)

    return gen_feedback

def df_feedback_file_distributed(filename_nd, start_timestamp: float, end_timestamp: float, category: str, measure: Optional[str]=None, room: Optional[str]=None):
 
    df = pd.DataFrame(data=generator_feedback_keyvalue_from_csv_file(filename_nd))
    df['date'] = pd.to_datetime(df['date'])
    middle = df[(
        (df['timestamp'] >= start_timestamp)
        & (df['timestamp'] <= end_timestamp)
        & (df['category'] == category)
    )]
    if (middle.shape[0] > 0):
        middle['measure'] = middle.apply(lambda row: cfg.get_measure_list_from_reasons(row['reasonsList']), axis=1)
 
    return middle


def flatten_feedback_dict(feedback_dict, category=cfg.get_config().data.feedback.category) -> List[dict]:
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


def firebase_feedback_reading(start_date: datetime, end_date: datetime, category: str, measures: Optional[List[str]], rooms: Optional[List[str]] = None):

    def generator_flatten_feedback(docref_stream):
        for doc_ref in docref_stream:
            doc_dict = doc_ref.to_dict()
            for vote in flatten_feedback_dict(doc_dict, category=category):
                vote['measure'] = cfg.get_measure_list_from_reasons(vote['reasonsList'])
                if rooms and not vote['room'] in rooms:
                    continue
                if category and vote['category'] != category:
                    continue
                if measures:
                    for measure in measures:
                        if not any([reason in cfg.get_reasons_for_measure(measure) for reason in vote['reasonsList']]):
                            continue
                yield vote

    firebase_collection = get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection).where('date','>=',start_date).where('date','<=',end_date)
#    gen_feedback = generator_flatten_feedback(firebase_collection.stream(), category=category)

    return [vote_dict for vote_dict in generator_flatten_feedback(firebase_collection.stream())]


def get_rooms():
    rooms = set()
    firebase_collection = get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection)
    for v in firebase_collection.stream():
        rooms.add(v.to_dict().get('class', None))
    return list(rooms)


def get_max_date():
    firebase_collection = get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection)
    query = firebase_collection.order_by("date", direction=firestore.Query.ASCENDING).limit(1)
    result = query.get()

    return result


def get_min_date():
    firebase_collection = get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection)
    query = firebase_collection.order_by("date", direction=firestore.Query.DESCENDING).limit(1)
    result = query.get()

    return result
