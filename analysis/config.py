from typing import Literal, Optional
import os

import yaml
from dotenv import load_dotenv
import pydantic

DatasourceType = Literal['mongo', 'firebase', 'csv']
DaskClusterType = Literal['single-threaded', 'synchronous', 'process', 'distributed']

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
