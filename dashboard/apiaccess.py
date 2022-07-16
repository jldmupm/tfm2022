from typing import Dict, List
import pandas as pd

import httpx

from sklearn.linear_model import LogisticRegression

import analysis.config as cfg
from analysis.process.analyze import logistic_regression_from_json

URL_ROOMS = cfg.get_api_url() + '/api/v1/rooms'
URL_MEASURES = cfg.get_api_url() + '/api/v1/measures'
URL_VOTES = cfg.get_api_url() + '/api/v1/feedback/timeline'
URL_SENSOR = cfg.get_api_url() + '/api/v1/sensorization/timeline'
URL_MERGED = cfg.get_api_url() + '/api/v1/merge/timeline'
URL_ANALISYS = cfg.get_api_url() + '/api/v1/analysis/linear-regression'    

empty_merged_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min_sensor':[], 'value_mean_sensor':[], 'value_max_sensor':[], 'value_std_sensor':[], 'value_count_sensor':[], 'value_min_vote':[], 'value_mean_vote':[], 'value_max_vote':[], 'value_std_vote':[], 'value_count_vote':[]}

empty_merged_dataframe = pd.DataFrame(empty_merged_data_set)

client = httpx.Client(timeout=None)

def check_status_code(response: httpx.Response) -> bool:
    return response.status_code in [200]


def get_merged_data(start_date: str, end_date: str, measure=None, room=None, tg='1H') -> dict:
    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg}

    r_merged = client.post(URL_MERGED, json=data_request)

    result: dict = empty_merged_dataframe.to_dict(orient='list')
    if check_status_code(r_merged):
        result = r_merged.json()

    return result


def get_all_rooms() -> List[str]:
    r_all_rooms = client.get(URL_ROOMS)
    if check_status_code(r_all_rooms):
        return r_all_rooms.json()['rooms']
        
    return []


def get_all_measures() -> List[str]:
    r_all_measures = client.get(URL_MEASURES)
    if check_status_code(r_all_measures):
        return r_all_measures.json()['measures']
    
    return []


def get_lr_model(start_date: str, end_date: str, measure=None, room=None, tg='2H') -> Dict[str, LogisticRegression]:
    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg, 'test_size': 0.3}
    r_analisis = httpx.post(URL_ANALISYS, json=data_request, timeout=None)

    result = {}
    if r_analisis.status_code in [200]:
        models = {}
        result = r_analisis.json()
        for k in result['models'].keys():
            lr = logistic_regression_from_json(result['models'][k]['model'])
            models[k] = lr

    return result
