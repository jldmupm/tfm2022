from typing import List

from dask.distributed import get_worker, Worker
import dask.bag as db

import src.feedback.fb_source as fb
import src.sensors.mg_source as mg

import src.config as cfg

MergeVoteWithMeasuresAvailableFields = ['type', 'subjectId', 'date', 'duration', 'room', 'reasonString', 'category', 'score', 'reasonsList', 'timestamp', 'sensor', 'sensor_type', 'sensor_id', 'sensor_avg', 'sensor_count', 'sensor_min', 'sensor_max']

# una solución más completa: https://stackoverflow.com/questions/60716000/how-to-create-a-database-connect-engine-in-each-dask-sub-process-to-parallel-tho
def worker_setup(dask_worker: Worker):
    dask_worker.votedbconfig = cfg.datasources['sensors']
    dask_worker.votedb = mg.get_mongodb_database(cfg.datasources['sensors'])[cfg.datasources.get('collection','reading')]
    
def list_votes_with_sensor_data(feedback_record: dict, group_id_type: mg.GROUP_SENSORS_USING_TYPE) -> List[dict]:
    # EXCLUDE_MEASURE_FIELDS = ['_id']

    mongo_client = get_worker().votedb

    sensors_in_range_and_room_of_vote = mg.get_average_sensor_data(mongo_client, feedback_record['date'], feedback_record['duration'], feedback_record['room'], group_id_type)
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

def bag_loader_from_file(feedback_file: str) -> db.Bag:
    gen_feedback = fb.generator_feedback_keyvalue_from_csv_file(filename=feedback_file)
    dbag_feedback = db.from_sequence(gen_feedback)
    return dbag_feedback

def bag_loader_from_firebase(firebase_config: dict) -> db.Bag:
    stream = fb.get_firestore_db_client(firebase_config).collection(firebase_config.get('collection')).stream()
    gen_feedback = (docRef.to_dict() for docRef in stream)
    dbag_feedback = db.from_sequence(gen_feedback)
    return dbag_feedback

def merge_from_file(filename: str):
    bag = bag_loader_from_file(filename)
    snd = bag.map(list_votes_with_sensor_data, group_id_type='group_single_sensor').flatten().filter(lambda e: e.get('sensor', False))

    return snd

def merge_from_database(config: dict):
    bag = bag_loader_from_firebase(firebase_config=config).map(fb.flatten_feedback_dict).flatten()
    snd = bag.map(list_votes_with_sensor_data, group_id_type='group_single_sensor').flatten().filter(lambda e: e.get('sensor', False))

    return snd


if __name__ == '__main__':
    import src.dask.setup_client
    src.dask.setup_client.setup()
    snd = merge_from_file('./db/all_feedback_data.csv')
#    snd = merge_from_database(config=datasource.FIREBASE_SOURCE_CONFIG[0])
    
    res = snd.compute()
    for b in res:
        print(b)
        print(".....................")
    print("==============================")
    print(len(res))
