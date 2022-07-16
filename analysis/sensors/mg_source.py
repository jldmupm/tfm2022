from datetime import datetime, timedelta
import logging
from typing import Literal, List, Optional

import analysis.config as cfg

import pymongo
import numpy as np
import pandas as pd

import analysis.config as cfg

GROUP_SENSORS_USING_TYPE =Literal['group_kind_sensor', 'group_single_sensor']

FlattenSensorFieldsList = ['type', 'id', 'custom_id', 'time', 'room', 'hub', 'node', 'sensor', 'value', 'timestamp', 'date']


def get_metadata() -> pd.DataFrame:
    meta = pd.DataFrame([], columns=FlattenSensorFieldsList)
    meta.type = meta.type.astype(str)
    meta.id = meta.id.astype(np.number)
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


def get_mongodb_cli(connection_string: str = None):
    """Return a MongoDB Client as configured.

    :returns:
      A MongoDB client.
    """
  
    connection_string = connection_string if connection_string is not None else cfg.get_mongodb_connection_string()
    mongodb_client = pymongo.MongoClient(connection_string)

    return mongodb_client


def get_mongodb_collection(connection_string: str = None,  database: str = None, collection: str = None):
    """Return a MongoDB Collection for sensors as configured.

    :param collection:
      MongoDB selected collection.
    :returns:
      A MongoDB collection.
    """
  
    current_config = cfg.get_config()
    collection = collection if collection else current_config.datasources.sensors.collection
    database = database if database else current_config.datasources.sensors.database
    mongodb_client = get_mongodb_cli(connection_string)
    mongo_collection = mongodb_client[database][collection]
    return mongo_collection


def get_average_sensor_data(mongo_sensor_collection,
                            feedback_timestamp: float,
                            feedback_duration: int,
                            feedback_room: str,
                            group_type: GROUP_SENSORS_USING_TYPE):
    """
    Given the data of a vote it returns the average readings for each indidual or type of sensor.

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
      A list with the average, minimum, maximum, count, number of samples and standard deviation for each sensor/kind of sensor.
    """
  
    def query_average_sensor_data(
                            feedback_timestamp: float,
                            feedback_duration: int,
                            feedback_room: str,
                            group_type: GROUP_SENSORS_USING_TYPE = 'group_kind_sensor'):
        sensor_id = {
            'group_single_sensor': { 'sensor': '$sensor' },
            'group_kind_sensor': {'class': '$class',
                                  'hub': '$hub',
                                  'node': '$node',
                                  'sensor': '$sensor'}
        }[group_type]
        start_date = datetime.fromtimestamp(feedback_timestamp)
        start = start_date
        end = start_date + timedelta(hours=feedback_duration)
        FILTER={
            '$and': [
                { 'class': { '$eq': feedback_room } },
                { 'time': {'$gte': start} },
                { 'time': {'$lte': end} }
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
                'r_count': {
                    '$sum': 1
                },
                'r_avg': {
                    '$avg': '$value'
                },
                'r_max': {
                    '$max': '$value'
                },
                'r_min': {
                    '$min': '$value'
                },
                'r_std': {
                    '$stdDevSamp': '$value'
                }
            }
        }
        cursor = mongo_sensor_collection.aggregate(
            pipeline=[{ '$match': FILTER }, *EXPAND, GROUP]
        )

        matching_readings = [{
            **sdata,
            'sensor_type': sdata['_id']['sensor'],
            'sensor_id': '@'.join(sdata['_id'].values()),
        } for sdata in cursor]
        return matching_readings

    return query_average_sensor_data(feedback_timestamp,
                                     feedback_duration,
                                     feedback_room,
                                     group_type)


# ALL SENSOR DATA


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
            "date": datetime.fromtimestamp(float(timestamp)).replace(tzinfo=None),
        }
        lst_dicts.append(new_key_value_dict)

    return lst_dicts


def get_all_sensor_data(mongo_sensor_collection, filters=None):
    """
    Return all the data retrieved from sensors.
    """
    cursor = mongo_sensor_collection.find(filters)
    return cursor

def get_filtered_sensor_data(mongo_sensor_collection, filters={}):
    """
    Return all the data retrieved from sensors.
    """
    cursor = mongo_sensor_collection.find(filters)
    return cursor


def generator_from_mongo_cursor(mg_cursor):
 
    for elem in mg_cursor:
        for sensor_reading in flatten_sensor_dict(elem):
            yield sensor_reading


def compose_data_sensor_type_query(list_sensor_types: List[str]) -> dict:
    result = {}
    sensor_query = [{f'data.{sensor}': {'$exists': 'true'}} for sensor in list_sensor_types]
    if len(sensor_query) > 0:
        result = {'$or': sensor_query}
    return result


def mongo_distributed_sensor_reading(date, num_days: int, sensor_types: List[str] = [], room: Optional[str] = None):
    mongo_collection = get_mongodb_collection()
    min_date = date
    max_date = date + timedelta(days=num_days)
    filters = {
            '$and': [
                { 'time': {'$gte': min_date} },
                { 'time': {'$lte': max_date} },
            ]
    }
    if room:
        filters['$and'] = [*filters['$and'], { 'class': { '$eq': room }}]
    if sensor_types:
        filters['$and'] = [*filters['$and'], compose_data_sensor_type_query(sensor_types)]

    logging.debug(f'mongo_distributed_sensor_reading {filters=}')
    return pd.DataFrame(data=generator_from_mongo_cursor(get_filtered_sensor_data(mongo_collection, filters=filters)))

def mongo_sensor_reading(min_datetime: datetime, max_datetime: datetime, sensor_types: List[str] = [], room: Optional[str] = None) -> 'Cursor':
    logging.debug(f'mongo_sensor_reading {min_datetime=} {max_datetime=} {sensor_types=} {room=}')
    mongo_collection = get_mongodb_collection()
    filters = {
            '$and': [
                { 'time': {'$gte': min_datetime} },
                { 'time': {'$lte': max_datetime} },
                # filter out errors:
                { 'data': {'$exists': True }},
                { 'data': {'$ne': {}}},
            ]
    }
    if room:
        filters['$and'] = [*filters['$and'], { 'class': { '$eq': room }}]
    if sensor_types:
        filters['$and'] = [*filters['$and'], compose_data_sensor_type_query(sensor_types)]

    logging.debug(f'mongo_sensor_reading {filters=}')
    cursor = get_filtered_sensor_data(mongo_collection, filters=filters)
 
    return cursor
