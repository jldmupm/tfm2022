import fastapi
from fastapi.param_functions import Depends

import analysis.config as cfg
import api.models
import api.services as services

analysis_router = fastapi.APIRouter(responses={400: {"model": api.models.ErrorResponse}, 500: {"model": api.models.ErrorResponse}})


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
        response = {'dt': [], 'measure': [], 'room': [], 'value_min': [], 'value_max': [], 'value_mean': [], 'value_std': []}
    
    return response


@analysis_router.post('/sensorization/timeline', response_model=api.models.SensorizationTimelineResponse)
async def api_get_sensor_timeline(result=Depends(services.get_sensor_timeline)):
    if not result.empty:
        response = result.to_dict(orient='list')
    else:
        response = {'dt': [], 'measure': [], 'room': [], 'value_min': [], 'value_mean': [], 'value_max': [], 'value_std': []}
    
    return response

