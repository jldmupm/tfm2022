from typing import Generator, Tuple
from datetime import timedelta

import src.feedback.fs_source as fs
import src.feedback.models as models

import src.analisis.df_load as df_load

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
    firestore_db = fs.get_firestore_db_client()
    print('BEGIN')
    print('=========== Acceso directo a Firestore')
    feedback_stream = read_feedbacks(firestore_db, room='3203', limit=1).stream()
    for docRef in feedback_stream:
        print(docRef.id, docRef.to_dict()["date"], docRef.to_dict()["room"])

    print('=========== Obtener un generador the tuplas filtrados')
    for vote in fs.generator_feedback_keyvalue_from_stream_docref(fs.get_stream_docref(filters=[('room','==','CIC-3')],
                                             limit=12)):
        print('-'*8)
        print(vote)

    print('=========== Obtener un DataFrame de Pandas')
    df = df_load.load_feedback_dataframe(filters=[('room', '==', '1001')], limit=10)
    print(df)
    print('END')
