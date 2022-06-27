from typing import Generator, Tuple
from datetime import datetime, timedelta

import analysis.config as cfg
import analysis.feedback.fb_source as fb
import analysis.feedback.models as fb_models

def read_feedbacks(firestore_db, date = None, duration=None, room=None, projectId=None, limit=None):
    query = firestore_db.collection('feedback')
    if date:
        query = query.where('date', '>', date)
        if duration:
            query.where('date','<=',date + timedelta(hours=duration))
    if room:
        query = query.where('room', '==', room)
    if projectId:
        query = query.where('projectId', '==', projectId)
    if limit:
        query = query.limit(limit)
    return query


if __name__ == '__main__':
    firestore_db = fb.get_firestore_db_client()
    print('BEGIN')
    print('=========== Acceso directo a Firestore')
    feedback_stream = read_feedbacks(firestore_db, room='3203', limit=1).stream()
    for docRef in feedback_stream:
        print(docRef.id, docRef.to_dict()["date"], docRef.to_dict()["room"])

    print('=========== Obtener un generador the tuplas filtrados')
    for vote in fb.generator_feedback_keyvalue_from_firebase(cfg.get_config().datasources.feedbacks.collection, datetime.utcnow().timestamp() - timedelta(days=10), datetime.utcnow().timestamp())
        print('-'*8)
        print(vote)
    print('END')
