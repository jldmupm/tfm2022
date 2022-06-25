import datetime
from pprint import pprint
from typing import Literal, List, Union

import pymongo
import numpy as np
import pandas as pd

import analysis.config as cfg

GROUP_SENSORS_USING_TYPE =Literal['group_kind_sensor', 'group_single_sensor']

FlattenSensorFieldsList = ['type', 'id', 'custom_id', 'time', 'room', 'hub', 'node', 'sensor', 'value', 'timestamp', 'date']

def get_metadata() -> pd.DataFrame:
    meta = pd.DataFrame([], columns=FlattenSensorFieldsList)
    meta.type = meta.type.astype(str)
    meta.id = meta.type.astype(np.number)
    meta.custom_id = meta.custom_id.astype(str)
    meta.time = meta.time.astype(np.datetime64).tz_localize(None)
    meta.room = meta.room.astype(str)
    meta.hub = meta.hub.astype(str)
    meta.node = meta.node.astype(str)
    meta.sensor = meta.sensor.astype(str)
    meta.value = meta.value.astype(np.number)
    meta.timestamp = meta.timestamp.astype(np.number)
    meta.date = meta.date.astype(np.datetime64).tz_localize(None)
    
    return meta

def get_mongodb_cli():
    """Return a MongoDB Client as configured.

    :returns:
      A MongoDB client.
    """
    mongodb_client = pymongo.MongoClient(cfg.get_mongodb_connection_string())

    return mongodb_client

def get_mongodb_collection(colletion: str = cfg.get_config().datasources.sensors.collection, **kwargs):
    """Return a MongoDB Collection for sensors as configured.

    :param collection:
      MongoDB selected collection.
    :returns:
      A MongoDB collection.
    """
    sensors_datasource_config = cfg.get_config().datasources.sensors
    mongodb_client = get_mongodb_cli()
    mongo_collection = mongodb_client[sensors_datasource_config.database][colletion]
    return mongo_collection

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
        new_key_value_dict = {
            "type": "sensor",
            "id": sensor_data['_id'],
            "custom_id": custom_id,
            "time": sensor_data['time'].replace(tzinfo=None),
            "room": sensor_data['class'],
            "hub": sensor_data['hub'],
            "node": sensor_data['node'],
            "sensor": sensor,
            "value": value,
            "timestamp": timestamp,
            "date": datetime.datetime.fromtimestamp(float(timestamp)).replace(tzinfo=None),
        }
        lst_dicts.append(new_key_value_dict)

    return lst_dicts

def get_average_sensor_data(mongo_sensor_collection,
                            feedback_date: datetime.datetime,
                            feedback_duration: int,
                            feedback_room: str,
                            group_id: GROUP_SENSORS_USING_TYPE = 'group_kind_sensor'):
    """
    Returns the average readings for each indidual or type of sensor.

    :param mongo_sensor_collection:
      A Mongo collection with the sensor data.
    :param feedback_date:
      The datetime to get the sensor information.
    :param feedback_duration:
      The time in hours, to retrieve sensor data.
    :param feedback_room:
      The room to retrieve sensor data from.
    :param group_id:
      A string with the type of data agrupation:
         - 'group_kind_sensor': group the data for kind of sensor.
         - 'group_single_sensor': group the data for each individual sensor.
    :returns:
      A list with the average, min, max, count for each sensor/kind of sensor.
    """
    def get_average_sensor_data_aux(
                            feedback_date: datetime.datetime,
                            feedback_duration: int,
                            feedback_room: str,
                            group_id: GROUP_SENSORS_USING_TYPE = 'group_kind_sensor'):
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
            '$and': [
                { 'class': { '$eq': feedback_room } },
                { 'time': {'$gte': start} },
                { 'time': {'$lt': end} }
            ]
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
                },
                'std': {
                    '$stdDevSamp': '$value'
                }
            }
        }
        cursor = mongo_sensor_collection.aggregate(
            pipeline=[{ '$match': FILTER }, *EXPAND, GROUP]
        )

        matching_readings = [{**sdata} for sdata in cursor]
        return matching_readings

    return get_average_sensor_data_aux(feedback_date,
                                       feedback_duration,
                                       feedback_room,
                                       group_id)

def get_all_sensor_data(mongo_sensor_collection, filters=None):
    """
    Return all the data retrieved from sensors.
    """
    cursor = mongo_sensor_collection.find(filters)
    return cursor

def generator_from_mongo_cursor(mg_cursor):
    for elem in mg_cursor:
        for sensor_reading in flatten_sensor_dict(elem):
            yield sensor_reading

def mongo_distributed_sensor_reading(x, size=0):
    mongo_collection = get_mongodb_collection()
    return pd.DataFrame(data=generator_from_mongo_cursor(get_all_sensor_data(mongo_collection, filters=x)))
