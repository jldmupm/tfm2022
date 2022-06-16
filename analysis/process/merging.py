from typing import List

from dask.distributed import get_worker
import dask.bag as dbag

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg

import analysis.config as cfg

MergeVoteWithMeasuresAvailableFields = ['type', 'subjectId', 'date', 'duration', 'room', 'reasonsString', 'category', 'score', 'reasonsList', 'timestamp', 'sensor', 'sensor_type', 'sensor_id', 'sensor_avg', 'sensor_count', 'sensor_min', 'sensor_max']
    
def _list_votes_with_sensor_data(feedback_record: dict, group_id_type: mg.GROUP_SENSORS_USING_TYPE) -> List[dict]:
    mongo_client = get_worker().sensor_db
    mongo_sensor_collection = get_worker().sensor_db_collection
    sensors_in_range_and_room_of_vote = mg.get_average_sensor_data(mongo_sensor_collection,
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

def apply_feedback_filters(bag: dbag.Bag, **kwargs):
    res_bag = bag
    if kwargs.get('category', False):
        res_bag = res_bag.filter(lambda e: e.get('category', None) == kwargs.get('category'))
    return res_bag

def bag_loader_from_file(feedback_file: str, **kwargs) -> dbag.Bag:
    gen_feedback = fb.generator_feedback_keyvalue_from_csv_file(filename=feedback_file)
    dbag_feedback = dbag.from_sequence(gen_feedback)
    filtered_bag = apply_feedback_filters(dbag_feedback, **kwargs)
    return filtered_bag

def bag_loader_from_firebase(**kwargs) -> dbag.Bag:
    stream = fb.get_firestore_db_client().collection(cfg.get_config().datasources.feedbacks.collection).stream()
    gen_feedback = (docRef.to_dict() for docRef in stream) # TODO: 1: or map in the bag?
    dbag_feedback = dbag.from_sequence(gen_feedback).map(fb.flatten_feedback_dict).flatten() # TODO: 2: or map in the generator?
    filtered_bag = apply_feedback_filters(dbag_feedback, **kwargs)
    return filtered_bag

def merge_from_file(filename: str, group_id_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', **kwargs) -> dbag.Bag:
    bag = bag_loader_from_file(filename)
    filtered_bag = apply_feedback_filters(bag, **kwargs)
    snd = filtered_bag.map(_list_votes_with_sensor_data, group_id_type=group_id_type).flatten().filter(lambda e: e.get('sensor', False))

    return snd

def merge_from_database(feedback_bag: dbag.Bag, group_id_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', **kwargs) -> dbag.Bag:
    filtered_bag = apply_feedback_filters(feedback_bag, **kwargs)
    snd = filtered_bag.map(_list_votes_with_sensor_data, group_id_type=group_id_type).flatten().filter(lambda e: e.get('sensor', False))

    return snd
