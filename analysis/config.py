from typing import Literal, Optional
import os
from os.path import exists
from pydantic import fields

import yaml
from dotenv import load_dotenv
import pydantic
import cachey

__TFM2022_VERSION__ = '0.3.0'

config = None

cache = cachey.Cache(1e9, 1)

custom_dask_client = None

DatasourceType = Literal['mongo', 'firebase', 'csv']

# Config Models

class DataSourceMongoDB(pydantic.BaseModel):
    _type: DatasourceType = pydantic.Field('mongo', alias="type")
    host: str = pydantic.Field(default='localhost')
    database: str
    port: int = pydantic.Field(default=27017)
    collection: str
    auth_mechanism: str

class DataSourceFirebaseDB(pydantic.BaseModel):
    _type: str = pydantic.Field('firebase', alias="type")
    collection: str
    
class DataSourceType(pydantic.BaseModel):
    sensors: DataSourceMongoDB
    feedbacks: DataSourceFirebaseDB

class CredentialsType(pydantic.BaseModel):
    mongodb: dict
    firebase: dict

class ClusterType(pydantic.BaseModel):
    scheduler: str = "processes"
    distributed: str
    partitions: int = 2
    workers: int = 4
    
class ConfigType(pydantic.BaseModel):
    datasources: DataSourceType
    credentials: CredentialsType
    cluster: ClusterType
    
def _get_env_credentials():
    return {
        'mongodb': {
            'username': os.environ.get('MONGODB_SENSOR_USERNAME',None),
            'password': os.environ.get('MONGODB_SENSOR_PASSWORD',None),
        },
        'firebase': {
            'keypath': os.environ.get('FIREBASE_FEEDBACK_KEYPATH',None)
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
        'collection': os.environ.get('FIREBASE_COLLECTION', feedback_in_file.get('collection', None))
    }

def _get_cluster_config(data_in_conf_file: dict):
    cluster_in_file = data_in_conf_file.get('cluster', {})
    return {
        **cluster_in_file,
        'scheduler': os.environ.get('SCHEDULER_TYPE', cluster_in_file.get('scheduler', None)),
        'distributed': os.environ.get('SCHEDULER_DISTRIBUTED_URL', cluster_in_file.get('distributed', None)),
    }

def get_config(config_filename: str = './defaults.yml', force=False) -> Optional[ConfigType]:
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

    load_dotenv()
    data = {}
    if force or config is None:
        if exists(config_filename):
            with open(config_filename, 'r') as cfg_file:
                data = yaml.safe_load(cfg_file)
        config = ConfigType.parse_obj({
            'datasources': {
                'sensors': _get_mongo_config(data),
                'feedbacks': _get_firebase_config(data),
            },
            'cluster': _get_cluster_config(data),
            'credentials': _get_env_credentials(),
        })
    return config

def get_version():
    return __TFM2022_VERSION__

def get_mongodb_connection_string() -> str:
    """Gets a MongoDB connection string.
    
    :returns:
      A MongoDB string as configured.
    """
    the_current_config: Optional[ConfigType] = get_config()
    mongo = the_current_config.datasources.sensors
    credentials = the_current_config.credentials.mongodb
    connection_string = f"mongodb://{credentials['username']}:{credentials['password']}@{mongo.host}:{mongo.port}/{mongo.database}?retryWrites=true{mongo.auth_mechanism}"
    return connection_string

def get_firebase_file_credentials() -> Optional[str]:
    """Gets the Firebase credentials.

    :returns:
      A path to the configured Firebase credentials.
    """
    return  get_config().credentials.firebase.get('keypath', None)

def set_cluster_client(client):
    global custom_dask_client
    custom_dask_client = client

def get_cluster_client():
    """
    Returns a Dask Scheduler client.
    """
    global custom_dask_client
    yield custom_dask_client

def fileForFeedback():
    file_feedback = os.environ.get('USE_FILE_INSTEAD_OF_FIRESTORE', '')
    return file_feedback
