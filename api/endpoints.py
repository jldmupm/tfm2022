import fastapi
from fastapi.param_functions import Depends
import pandas as pd

import analysis.config as cfg
import api.models
import api.services as services

analysis_router = fastapi.APIRouter(responses={400: {"model": api.models.ErrorResponse}, 500: {"model": api.models.ErrorResponse}})

empty_single_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min':[], 'value_mean':[], 'value_max':[], 'value_std':[], 'value_count':[]}
empty_merged_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min_sensor':[], 'value_mean_sensor':[], 'value_max_sensor':[], 'value_std_sensor':[], 'value_count_sensor':[], 'value_min_vote':[], 'value_mean_vote':[], 'value_max_vote':[], 'value_std_vote':[], 'value_count_vote':[]}

@analysis_router.get('/version', response_model=str)
async def api_get_version():
    """
    Returns the version of the Analysis System.
    """
    return cfg.get_version()


@analysis_router.get('/rooms', response_model=api.models.RoomList)
async def api_get_feedback_and_sensors_rooms(result=Depends(services.get_rooms)):
    return result


@analysis_router.get('/measures', response_model=api.models.MeasureList)
async def api_get_measures(result=Depends(services.get_measures)):
    return result


@analysis_router.get('/configuration', response_model=api.models.ConfigResponse)
async def api_get_configuration():
    return cfg.get_config()


@analysis_router.post('/feedback/timeline', response_model=api.models.FeedbackTimelineResponse)
async def api_get_feedback_timeline(result=Depends(services.get_feedback_timeline)):
    if not result.empty:
        response = result.to_dict(orient='list')
    else:
        response = empty_single_data_set
    
    return response


@analysis_router.post('/sensorization/timeline', response_model=api.models.SensorizationTimelineResponse)
async def api_get_sensor_timeline(result=Depends(services.get_sensor_timeline)):
    if not result.empty:
        response = result.to_dict(orient='list')
    else:
        response = empty_single_data_set
    
    return response


def get_merged_timeline(df_sensor_data=Depends(services.get_sensor_timeline),
                        df_feedback_data=Depends(services.get_feedback_timeline)
):
    if not df_sensor_data.empty:
        df_sensor = df_sensor_data.reset_index()
    else:
        df_sensor = pd.DataFrame(empty_single_data_set)
    if not df_feedback_data.empty:
        df_feedback = df_feedback_data.reset_index()
    else:
        df_feedback = pd.DataFrame(empty_single_data_set)
    df_merged_data = df_sensor.merge(df_feedback,
                                     how='outer',
                                     suffixes=("_sensor", "_vote"),
                                     on=['dt', 'room', 'measure']
                                     )
    df_merged_data = df_merged_data.fillna(value=0)
    df_merged_data.reset_index()
    if not df_merged_data.empty:
        result = df_merged_data.to_dict(orient='list')
    else:
        result = empty_merged_data_set

    return result


@analysis_router.post('/merge/timeline', response_model=api.models.MergedTimelineResponse)
async def api_get_merged_timeline(result = Depends(get_merged_timeline)):
    return result

# @analysis_router.post('/merge/analysis/k-means')
# async def api_get_kmeans_analysis():
