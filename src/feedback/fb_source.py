# -*- coding: utf-8 -*-
from typing import Any, Generator, Iterable, List, Optional, Tuple
import csv

import dateutil.parser
import firebase_admin
from firebase_admin import firestore

from src.utils import utils

FlattenVoteFieldsList = ['type', 'id', 'subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp']

FirestoreFilterType = Tuple[str, str, str] # TODO: improve

def get_firestore_db_client(firebase_config) -> firebase_admin.App:
    "Get a Firestore Client"
    cred = utils.get_firebase_credentials(firebase_config)
    default_app = firebase_admin.initialize_app(cred)
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
            feedback['date'] = dateutil.parser.parse(feedback['date'])
            # ups!
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
        new_key_value_dict = {"type": "feeback", **feedback_dict, **vote, "timestamp": feedback_dict['date'].timestamp()}
        del new_key_value_dict['votingTuple']
        lst_dicts.append(new_key_value_dict)

    return lst_dicts
