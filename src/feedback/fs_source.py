# -*- coding: utf-8 -*-
from typing import Generator, List, Tuple

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

import src.config as config
from src.feedback.models import Survey, AvailableFieldsList

FirestoreFilterType = Tuple[str, str, str] # TODO: improve

firestore_db = None

def get_firestore_db_client():
    "Get a Firestore Client"
    global firestore_db
    if not firestore_db:
        # Authentication is not needed if accessing from Google Cloud.
        cred = credentials.Certificate(config.KEY)
        default_app = firebase_admin.initialize_app(cred)
        firestore_db = firestore.client()
    
    return firestore_db

def get_stream_docref(filters: List[FirestoreFilterType] = [], order_by: str =None, limit: int = None, limit_to_last: int = None, collection='feedback') -> 'Stream':
    "Get a filtered stream of Firestore DocumentRef from the collection"
    query = get_firestore_db_client().collection(collection)

    for filter in filters:
        query = query.where(*filter)

    if order_by:
        query = query.order_by(order_by)
        
    if limit:
        query = query.limit(limit)

    if limit_to_last:
        query = query.limit_to_last(limit_to_last)

    return query.stream()

# Functions to return plain dictionaries (key/value)

def spawn_generator_feedback_keyvalue_from_docref(docRef) -> List[dict]:
    "Convert a Firestore docRef containing survey information to a dictionary of Key/Value pairs."
    docref_dict = docRef.to_dict()
    lst_dicts = []
    for vote in docref_dict.get('votingTuple', []):
        for reason in vote.get('reasonsList', []):
            new_key_value_dict = {"id": docRef.id, **docref_dict, **vote, "reason": reason}
            del new_key_value_dict['votingTuple']
            del new_key_value_dict['reasonsList']
            lst_dicts.append(new_key_value_dict)

    return lst_dicts

def generator_feedback_keyvalue_from_stream_docref(stream) -> Generator[dict, None, None]:
    "Get a generator of 'Key/Value' objects from a Firestore stream"
    docRef = next(stream, None)
    while docRef:
        for vote in spawn_generator_feedback_keyvalue_from_docref(docRef):
            yield vote
        docRef = next(stream, None)

def generator_feedback_keyvalue(filters: List[FirestoreFilterType] = [], order_by: str = None, limit: int = None, limit_to_last: int = None) -> Generator[dict, None, None]:
    "Get a generator of filtered Key/Value dictionaries"
    return generator_feedback_keyvalue_from_stream_docref(get_stream_docref(filters=filters, order_by = order_by, limit=limit, limit_to_last=limit_to_last))

# Functions to return tuples of plain data

def transform_vote_to_tuple(vote: dict) -> Tuple:
    return tuple([vote[field] for field in AvailableFieldsList])

def spawn_feeback_tuple_from_generator_keyvalue(generator: Generator[dict, None, None]) -> Generator[tuple, None, None]:
    "Get a generator of Tuples from a Firestore stream"
    vote_dict = next(generator, None)
    while vote_dict:
        yield transform_vote_to_tuple(vote_dict)
        vote_dict = next(generator, None)

def generator_feedback_tuple(filters: List[FirestoreFilterType] = [], order_by: str  = None, limit: int = None, limit_to_last: int = None) -> Generator[tuple, None, None]:
    "Get a generator of filtered tuples"
    return spawn_feeback_tuple_from_generator_keyvalue(generator_feedback_keyvalue(filters=filters, order_by = order_by, limit=limit, limit_to_last=limit_to_last))

# Functions to return Survey pydantic objects

def generator_feedback_surveys_from_stream_of_docref(stream) -> Generator[Tuple[str, Survey], None, None]:
    "Gat a generator of 'Survey' objects from a Firestore Stream"
    print("*", end=" ")
    docRef = next(stream, None)
    while docRef:
        print("-", end=" ")
        yield (docRef.id, Survey(**docRef.to_dict()))
        docRef = next(stream, None)

def surveys_generator(filters: List[FirestoreFilterType] = [], order_by: str = None, limit: int = None, limit_to_last: int = None) -> Generator[Tuple[str, Survey], None, None]:
    "Get a generator of queried/filtered 'Survey' objects"
    return generator_feedback_surveys_from_stream_of_docref(get_stream_docref(filters=filters, order_by=order_by, limit=limit, limit_to_last=limit_to_last))
