from typing import Optional, Union
import os

import yaml
from dotenv import load_dotenv
import pydantic

class DataSourceType(pydantic.BaseModel):
    sensors: dict
    feedbacks: dict

class CredentialsType(pydantic.BaseModel):
    mongodb: Union[dict, str]
    firebase: Union[dict, str]
    
class Config(pydantic.BaseModel):
    datasources: DataSourceType
    credentials: CredentialsType
    dask: dict

config = None
    
def get_env_credentials():
    load_dotenv('.env')
    return {
        'mongodb': {
            'username': os.environ.get('MONGODB_SENSOR_USERNAME',''),
            'password': os.environ.get('MONGODB_SENSOR_PASSWORD',''),
        },
        'firebase': {
            'keypath': os.environ.get('./keys/tfm2022-72c94-firebase-adminsdk-ucaeg-60cfbff520.json','')
        }
    }

def get_config(config_filename: str = './conf/config.yml',
               force: bool=True) -> Optional[Config]:
    global config
    if not config or force:
        with open(config_filename, 'r') as file:
            data: dict = yaml.safe_load(file)
            config = Config.parse_obj({**data, 'credentials': get_env_credentials()})
    return config

def get_mongodb_connection_string() -> str:
    cfg: Optional[Config] = get_config()
    mongo = cfg.datasources.sensors
    credentials = cfg.credentials.mongodb
    connection_string = f"mongodb://{credentials['username']}:{credentials['password']}@{mongo.get('host','localhost')}:{mongo.get('port', 27017)}/{mongo['database']}?retryWrites=true{mongo.get('auth_mechanism','')}"
    print(connection_string)
    return connection_string

def get_firebase_credentials() -> str:
    cfg: Optional[Config] = get_config()
    return cfg.credentials.firebase['keypath']
    
get_config()
