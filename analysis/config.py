from typing import Literal, Optional
import os

import yaml
from dotenv import load_dotenv
import pydantic

import pymongo

from dask.distributed import Client, Worker, WorkerPlugin
from dask.distributed import PipInstall as PipInstallPlugin

import dask.config
import dask.distributed

DatasourceType = Literal['mongo', 'firebase', 'csv']
DaskClusterType = Literal['single-threaded', 'synchronous', 'process', 'distributed']

custom_dask_client = None

# Config Models

class DataSourceMongoDB(pydantic.BaseModel):
    _type: DatasourceType = pydantic.Field('mongo', alias="type")
    host: str = pydantic.Field(default='localhost')
    database: str
    port: int = pydantic.Field(default=27017)
    collection: str
    auth_mechanism: str

class DataSourceFirebaseDB(pydantic.BaseModel):
    _type = pydantic.Field('firebase', alias="type")
    collection: str
    
class DataSourceType(pydantic.BaseModel):
    sensors: DataSourceMongoDB
    feedbacks: DataSourceFirebaseDB

class CredentialsType(pydantic.BaseModel):
    mongodb: dict
    firebase: dict

class DaskConfigType(pydantic.BaseModel):
    scheduler_preconfig: DaskClusterType
    scheduler_url: str
    partitions: int
    
class ConfigType(pydantic.BaseModel):
    datasources: DataSourceType
    credentials: CredentialsType
    dask_cluster: DaskConfigType


# Dask Plugins

# TODO: prepare a custom Docker image with pymongo already installed
class WorkerDatasourcePlugin(WorkerPlugin):
    def __init__(self, mongodb_url: str, sensor_database: str, sensor_collection: str):
        self.mongodb_url = mongodb_url
        self.sensor_database = sensor_database
        self.sensor_collection = sensor_collection

    def setup(self, worker: Worker):
        print('hello', worker)
        sensor_db = pymongo.MongoClient(self.mongodb_url)
        worker.sensor_db = sensor_db
        worker.sensor_db_collection = sensor_db[self.sensor_database][self.sensor_collection]

    def teardown(self, worker: Worker):
        print("goodbye", worker)
        worker.sensor_db.close()

def _get_env_credentials():
    load_dotenv()
    return {
        'mongodb': {
            'username': os.environ.get('MONGODB_SENSOR_USERNAME',None),
            'password': os.environ.get('MONGODB_SENSOR_PASSWORD',None),
        },
        'firebase': {
            'keypath': os.environ.get('FIREBASE_FEEDBACK_KEYPATH',None)
        }
    }

def get_config(config_filename: str = './conf/config.yml') -> Optional[ConfigType]:
    """If not configuration has been loaded (or if forced), reads the
    {config_filename} configuration file, and get the credentials from
    the environment variables.

    Sets the module variable /config/ with the result.

    :param config_filename:
      Yaml configuration file.
    :returns:
      A ConfigType object with the configuration contained in the configuration file and the environment variables.

    """
    with open(config_filename, 'r') as file:
        data: dict = yaml.safe_load(file)
        config = ConfigType.parse_obj({**data, 'credentials': _get_env_credentials()})
        return config

def get_dask_client():
    global custom_dask_client
    if custom_dask_client is None:
        dask.config.set(scheduler=get_scheduler_preconfig()) # threads, processes, synchronous
        if get_scheduler_preconfig() in ['distributed']:
            # distributed. The scheduler.
            url_scheduler = get_scheduler_url()
            custom_dask_client = dask.distributed.Client(url_scheduler, name='tfm2022_distributed')
        else:
            custom_dask_client = dask.distributed.Client(name='tfm2022_non_distributed')
        url_string = get_mongodb_connection_string()
        sensor_database = get_config().datasources.sensors.database
        sensor_collection = get_config().datasources.sensors.collection
        dependencies_plugin = PipInstallPlugin(packages=["pymongo"], pip_options=["--upgrade"])
        worker_db_plugin = WorkerDatasourcePlugin(url_string, sensor_database, sensor_collection)
        custom_dask_client.register_worker_plugin(dependencies_plugin)
        custom_dask_client.register_worker_plugin(worker_db_plugin)

    return custom_dask_client
    
def get_mongodb_connection_string() -> str:
    """Gets a MongoDB connection string.
    
    :returns:
      A MongoDB string as configured.
    """
    cfg: Optional[ConfigType] = get_config()
    mongo = cfg.datasources.sensors
    credentials = cfg.credentials.mongodb
    connection_string = f"mongodb://{credentials['username']}:{credentials['password']}@{mongo.host}:{mongo.port}/{mongo.database}?retryWrites=true{mongo.auth_mechanism}"
    return connection_string

def get_firebase_file_credentials() -> Optional[str]:
    """Gets the Firebase credentials.

    :returns:
      A path to the configured Firebase credentials.
    """
    return  get_config().credentials.firebase.get('keypath', None)

def get_scheduler_preconfig() -> str:
    return get_config().dask_cluster.scheduler_preconfig

def get_scheduler_url() -> str:
    return get_config().dask_cluster.scheduler_url
