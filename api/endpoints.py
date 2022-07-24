from typing import Optional

import fastapi
from fastapi.param_functions import Depends

import analysis.config as cfg

import pandas as pd

import api.models
import api.services as services

analysis_router = fastapi.APIRouter(responses={400: {"model": api.models.ErrorResponse}, 422: {"model": api.models.ErrorResponse}, 500: {"model": api.models.ErrorResponse}})


@analysis_router.get('/version', response_model=str)
async def api_get_version():
    """
    Returns the version of the Analysis System.
    """
    return cfg.get_version()


@analysis_router.get('/configuration', response_model=api.models.ConfigResponse)
async def api_get_configuration(force_reload: bool=False):
    """
    Returns the current configuration.

    NOTE: the creedentials are keeped secret.
    """
    return cfg.get_config(force=force_reload)


@analysis_router.get('/rooms', response_model=api.models.RoomList)
async def api_get_feedback_and_sensors_rooms(result=Depends(services.get_rooms)):
    """
    Returns a list of all the rooms found in the measuremnts and score data.
    """
    return result


@analysis_router.get('/measures', response_model=api.models.MeasureList)
async def api_get_measures(result=Depends(services.get_measures)):
    """
    Returns a list of all the configured measures.
    """
    return result


@analysis_router.get('/date-range', response_model=api.models.DateRange)
async def api_get_date_range(result=Depends(services.get_date_range)):
    """
    Returns a list of all the configured measures.
    """
    return { 'min_date': result[0], 'max_date': result[1] }


@analysis_router.post('/feedback/timeline', response_model=api.models.FeedbackTimelineResponse)
async def api_get_feedback_timeline(result=Depends(services.get_feedback_timeline)):
    """
    Returns a timeline of average scores for each measure and room.
    """
    if not result.empty:
        response = result.to_dict(orient='list')
    else:
        response = services.empty_single_data_set
    
    return response


@analysis_router.post('/sensorization/timeline', response_model=api.models.SensorizationTimelineResponse)
async def api_get_sensor_timeline(result=Depends(services.get_sensor_timeline)):
    """
    Returns a timeline of avarage measurements for each measure and room.
    """
    if not result.empty:
        response = result.to_dict(orient='list')
    else:
        response = services.empty_single_data_set
    
    return response


@analysis_router.post('/merge/timeline', response_model=api.models.MergedTimelineResponse)
async def api_get_merged_timeline(df_merged_data = Depends(services.get_merged_timeline)):
    """
    Returns a timeline of the a score and average measurement for each room and measure.
    """

    if not df_merged_data.empty:
        result = df_merged_data.to_dict(orient='list')
    else:
        result = services.empty_merged_data_set
    return result


@analysis_router.post('/correlations/average/sensors', response_model=api.models.CorrelationMatrixResponse)
async def api_get_measurement_variable_correlations_average(result = Depends(services.get_measures_correlation_matrix_with_average)):
    """
    Returns the correlations of the measurement variables on their average values.
    """
    return result


@analysis_router.post('/correlations/average/sensors/scores')
async def api_get_measurement_variable_correlations_average_score(result = Depends(services.get_measures_correlation_matrix_with_scores)):
    """
    Returns the correlations of the measurement variables on their average values.
    """
    return result


@analysis_router.post('/analysis/linear-regression', response_model=api.models.LogisticRegressionResponse)
async def api_get_linear_regression_score(result = Depends(services.get_linear_regression)):
    """
    Returns the linear regression of the measuremt variables to get the score.
    """
    return result
    
