from typing import List, Literal, Optional, Union
import os
from os.path import exists
import pydantic

import yaml
from dotenv import load_dotenv
import pydantic

__TFM2022_VERSION__ = '0.4.0'

config = None

DatasourceType = Literal['mongo', 'firebase', 'csv']

Category = Literal['Ambiente']

# Config Models

class DataSourceMongoDB(pydantic.BaseModel):
    _type: DatasourceType = pydantic.Field('mongo', alias="type")
    host: str = pydantic.Field(default='localhost')
    database: str
    port: int = pydantic.Field(default=27017)
    collection: str
    auth_mechanism: str = '&authSource=admin&authMechanism=SCRAM-SHA-1'

class DataSourceFirebaseDB(pydantic.BaseModel):
    _type: str = pydantic.Field('firebase', alias="type")
    collection: str
    
class DataSourceType(pydantic.BaseModel):
    sensors: DataSourceMongoDB
    feedbacks: DataSourceFirebaseDB

class CredentialsType(pydantic.BaseModel):
    mongodb: dict
    firebase: dict
    redis: dict
    mongocache: dict
    
class ClusterType(pydantic.BaseModel):
    engine: str = "dask"
    scheduler_type: str = "processes"
    scheduler_url: str
    partitions: int = 2
    workers: int = 4

class AnalysisDataFeedbackType(pydantic.BaseModel):
    category: str
    sense: dict
    
class AnalysisDataType(pydantic.BaseModel):
    feedback: AnalysisDataFeedbackType
    sensors: dict

class CacheType(pydantic.BaseModel):
    host: str
    port: int
    database: str
    auth_mechanism: str = '&authSource=admin&authMechanism=SCRAM-SHA-1'
    collection: str
    
class ConfigType(pydantic.BaseModel):
    datasources: DataSourceType
    credentials: CredentialsType
    cluster: ClusterType
    data: AnalysisDataType
    cache: CacheType
    api: dict

def _get_env_credentials():
    return {
        'mongodb': {
            'username': os.environ.get('MONGODB_SENSOR_USERNAME',None),
            'password': os.environ.get('MONGODB_SENSOR_PASSWORD',None),
        },
        'mongocache': {
            'username': os.environ.get('MONGODB_CACHE_USERNAME',None),
            'password': os.environ.get('MONGODB_CACHE_PASSWORD',None),
        },
        'firebase': {
            'keypath': os.environ.get('FIREBASE_FEEDBACK_KEYPATH',None)
        },
        'redis': {
            'username': os.environ.get('REDIS_USER', None),
            'password': os.environ.get('REDIS_PASSWORD', None)
        }
    }


def _get_mongo_config(data_in_conf_file: dict):
    sensors_in_file = data_in_conf_file.get('datasources', {}).get('sensors', {})
    return {
        **sensors_in_file,
        'host': os.environ.get('MONGO_HOST', sensors_in_file.get('host', None)),
        'database': os.environ.get('MONGO_DATABASE', sensors_in_file.get('database', None)),
        'port': int(os.environ.get('MONGO_PORT', sensors_in_file.get('port', 27017))),
        'collection': os.environ.get('MONGO_COLLECTION', sensors_in_file.get('collection', None)),
        'auth_mechanism': os.environ.get('MONGO_AUTH_MECHANISM', sensors_in_file.get('auth_mechanism', '&authSource=admin&authMechanism=SCRAM-SHA-1'))
    }


def _get_firebase_config(data_in_conf_file: dict):
    feedback_in_file = data_in_conf_file.get('datasources',{}).get('feedbacks',{})
    return {
        'collection': os.environ.get('FIREBASE_COLLECTION', feedback_in_file.get('collection', None)),
    }


def _get_cluster_config(data_in_conf_file: dict):
    cluster_in_file = data_in_conf_file.get('cluster', {})
    result = {
        **cluster_in_file,
        'engine': os.environ.get('MODIN_ENGINE', cluster_in_file.get('engine', 'dask')),
        'scheduler_type': os.environ.get('SCHEDULER_TYPE', cluster_in_file.get('scheduler_type', None)),
        'scheduler_url': os.environ.get('SCHEDULER_URL', cluster_in_file.get('scheduler_url', None)),
    }
    os.environ['MODIN_ENGINE'] = result['engine']
    return result


def _get_data_config(data_in_conf_file: dict):
    return data_in_conf_file['data']


def _get_cache_config(data_in_conf_file: dict):
    cache_in_file = data_in_conf_file.get('cache',{}).get('mongo',{})
    return cache_in_file


def get_config(config_filename: str = './defaults.yml', force=False) -> ConfigType:
    """Returns the system configuration.

It gets the configuration from the environment variables and the config_filename parameter.

    :param config_filename:
      Yaml configuration file.
    :param force:
      Re-reads the configuration file.
    :returns:
      A ConfigType object with the configuration contained in the configuration file and the environment variables.

    """
    global config
    
    load_dotenv(override=False)
    conf_data = {}
    if force or config is None:
        if exists(config_filename):
            with open(config_filename, 'r') as cfg_file:
                conf_data = yaml.safe_load(cfg_file)
        config = ConfigType.parse_obj({
            'datasources': {
                'sensors': _get_mongo_config(conf_data),
                'feedbacks': _get_firebase_config(conf_data),
            },
            'cluster': _get_cluster_config(conf_data),
            'credentials': _get_env_credentials(),
            'data': _get_data_config(conf_data),
            'cache': _get_cache_config(conf_data),
            'api': conf_data.get('api', {'host': 'localhost', 'port':9080})
        })

    return config


def get_version():
    return __TFM2022_VERSION__


def get_firebase_file_credentials() -> Optional[str]:
    """Gets the Firebase credentials.

    :returns:
      A path to the configured Firebase credentials.
    """
    return  get_config().credentials.firebase.get('keypath', None)


def get_cluster() -> str:
    """
    Return the url of the scheduler for the cluster.
    """
    the_config = get_config()
    return the_config.cluster.scheduler_url


def fileForFeedback():
    """
    Return (if configured) the file to read the feedbacks from.
    """
    file_feedback = os.environ.get('USE_FILE_INSTEAD_OF_FIRESTORE', '')
    return file_feedback


def get_all_measures():
    return list(set(list(get_config().data.sensors.keys()) + list(get_config().data.feedback.sense.keys())))


def get_reasons_for_measure(measure: Optional[str]) -> List[str]:
    reasons = get_config().data.feedback.sense.get(measure, {})
    return reasons.get('pos',[]) + reasons.get('neg',[])


def get_sensors_for_measure(measure:Optional[str]) -> List[str]:
    sensors = get_config().data.sensors.get(measure,[])
    return sensors


def get_measure_from_reasons(reasons: List[str]) -> str:
    senses = get_config().data.feedback.sense
    for m in senses.keys():
        for s in reasons:
            if s in get_reasons_for_measure(m):
                return m
    return ''


def get_mongodb_connection_string() -> str:
    """Gets a MongoDB connection string for the case.
    
    :returns:
      A MongoDB string as configured.
    """
    the_current_config: Optional[ConfigType] = get_config()
    mongo = the_current_config.datasources.sensors
    credentials = the_current_config.credentials.mongodb
    connection_string = f"mongodb://{credentials['username']}:{credentials['password']}@{mongo.host}:{mongo.port}/{mongo.database}?retryWrites=true{mongo.auth_mechanism}"
    return connection_string


def get_mongodb_cache_connection_string() -> str:
    """Gets a MongoDB connection string.
    
    :returns:
      A MongoDB string as configured.
    """
    the_current_config: Optional[ConfigType] = get_config()
    mongo = the_current_config.cache
    credentials = the_current_config.credentials.mongocache
    connection_string = f"mongodb://{credentials['username']}:{credentials['password']}@{mongo.host}:{mongo.port}/{mongo.database}?retryWrites=true{mongo.auth_mechanism}"
    return connection_string


def get_measure_from_sensor(sensor: str) -> str:
    sensors = get_config().data.sensors
    for m in sensors.keys():
        if sensor in sensors[m]:
            return m
    return ''

def get_api_url() -> str:
    api_conf = get_config().api
    return f"http://{api_conf.get('host','localhost')}:{int(api_conf.get('port', '9080'))}"
