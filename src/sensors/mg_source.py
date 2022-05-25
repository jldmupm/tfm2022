import datetime
from typing import Literal, List, Union

import pymongo

from src.config import get_mongodb_connection_string

GROUP_SENSORS_USING_TYPE = Union[Literal['group_single_sensor'], Literal['group_kind_sensor']]

FlattenSensorFieldsList = ['type', 'id', 'custom_id', 'time', 'class', 'hub', 'node', 'sensor', 'value', 'timestamp', 'date']

def get_mongodb_database(mongo_config: dict):
    """Get a MongoDB Collection

    :param mongo_config:
      MongoDB configuration.
    :param collection:
      MongoDB selected collection, if None the configuration is used, if also None then return the DB.
    :returns:
      A MongoDB database mongo_client.
    """
    mongodb_client = pymongo.MongoClient(get_mongodb_connection_string())
    db_mongo = mongodb_client[mongo_config['database']]
    return db_mongo

def flatten_sensor_dict(sensor_data: dict) -> List[dict]:
    """Convert a MongoDB doc containing sensor information to a dictionary of Key/Value pairs.

    :param sensor_data:
      Sensor information to flatten.
    :returns:
      A list that contains the sensor_data with each sensor in a different element."""
    lst_dicts = []
    for sensor, value in sensor_data.get('data', {}).items():
        timestamp = sensor_data['time'].timestamp()
        custom_id = f"{sensor_data['class']}@{sensor_data['hub']}@{sensor_data['node']}@{sensor}"
        new_key_value_dict = {"type": "sensor", "custom_id": custom_id, **sensor_data, "sensor": sensor, "value": value, "timestamp": timestamp, "date": datetime.datetime.fromtimestamp(float(timestamp))}
        del new_key_value_dict['data']
        lst_dicts.append(new_key_value_dict)

    return lst_dicts

def get_average_sensor_data(mongo_client, feedback_date: datetime.datetime, feedback_duration: int, feedback_room: str, group_id: GROUP_SENSORS_USING_TYPE = 'group_kind_sensor'):
    sensor_id = {
        'group_single_sensor': { 'sensor': '$sensor' },
        'group_kind_sensor': {'class': '$class',
                              'hub': '$hub',
                              'node': '$node',
                              'sensor': '$sensor'}
    }[group_id]
    start = feedback_date
    end = feedback_date + datetime.timedelta(hours=feedback_duration)
    FILTER={
        'class': feedback_room,
        'time':  { '$gte': start, '$lt': end }
    }
    EXPAND=[
        {
            '$addFields': {
                'sensors_unwind': {
                    '$objectToArray': "$data"
                }
            }
        }, 
        {
            '$unwind':"$sensors_unwind"
        },
        {
            '$addFields': {
                'sensor': '$sensors_unwind.k',
                'value': '$sensors_unwind.v'
            }
        }
    ]
    GROUP={
        '$group': {
            '_id': sensor_id,
            'count': {
                '$sum': 1
            },
            'avg': {
                '$avg': '$value'
            },
            'max': {
                '$max': '$value'
            },
            'min': {
                '$min': '$value'
            }
        }
    }
    cursor = mongo_client.aggregate([{ '$match': FILTER }, *EXPAND, GROUP])

    return [sdata for sdata in cursor]
