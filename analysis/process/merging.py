from typing import List

from dask.distributed import get_worker
import dask.bag as dbag

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg

import analysis.config as cfg

MergeVoteWithMeasuresAvailableFields = ['type', 'subjectId', 'date', 'duration', 'room', 'reasonString', 'category', 'score', 'reasonsList', 'timestamp', 'sensor', 'sensor_type', 'sensor_id', 'sensor_avg', 'sensor_count', 'sensor_min', 'sensor_max']
    
def _list_votes_with_sensor_data(feedback_record: dict, group_id_type: mg.GROUP_SENSORS_USING_TYPE) -> List[dict]:
    mongo_client = get_worker().sensor_db
    sensors_in_range_and_room_of_vote = mg.get_average_sensor_data(mongo_client,
                                                                   feedback_record['date'],
                                                                   feedback_record['duration'],
                                                                   feedback_record['room'],
                                                                   group_id_type)
    feedback_record_mod = {k: v for k,v in feedback_record.items() if k in MergeVoteWithMeasuresAvailableFields}
    new_records = [{**feedback_record_mod,
                    'type': 'merge',
                    'date': feedback_record_mod['date'].replace(tzinfo=None),
                    'sensor': sensor['_id'],
                    'sensor_type': sensor['_id']['sensor'],
                    'sensor_id': "-".join(sensor['_id'].values()),
                    'sensor_avg': sensor['avg'],
                    'sensor_count': sensor['count'],
                    'sensor_min': sensor['min'],
                    'sensor_max': sensor['max'],
                    # 'measures': {k: v for k, v in sensor.items()
                    #              if k not in EXCLUDE_MEASURE_FIELDS}
                    }
                   for sensor in sensors_in_range_and_room_of_vote]

    return new_records

def bag_loader_from_file(feedback_file: str) -> dbag.Bag:
    gen_feedback = fb.generator_feedback_keyvalue_from_csv_file(filename=feedback_file)
    dbag_feedback = dbag.from_sequence(gen_feedback)
    return dbag_feedback

def bag_loader_from_firebase() -> dbag.Bag:
    stream = fb.get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection).stream()
    gen_feedback = (docRef.to_dict() for docRef in stream) # TODO: 1: or map in the bag?
    dbag_feedback = dbag.from_sequence(gen_feedback).map(fb.flatten_feedback_dict).flatten() # TODO: 2: or map in the generator?
    return dbag_feedback

def merge_from_file(filename: str):
    bag = bag_loader_from_file(filename)
    snd = bag.map(_list_votes_with_sensor_data, group_id_type='group_single_sensor').flatten().filter(lambda e: e.get('sensor', False))

    return snd

def merge_from_database():
    bag = bag_loader_from_firebase().map(fb.flatten_feedback_dict).flatten()
    snd = bag.map(_list_votes_with_sensor_data, group_id_type='group_single_sensor').flatten().filter(lambda e: e.get('sensor', False))

    return snd
