import fastapi
from fastapi.param_functions import Depends

import analysis.config as cfg
import analysis.api.models as models
import analysis.api.services as services

analysis_router = fastapi.APIRouter()

@analysis_router.get('/version', response_model=str)
def api_get_version():
    """
    Returns the version of the Analysis System.
    """
    return cfg.get_version()


@analysis_router.post('/correlation/score/avg', response_model=models.AnalysisResponseType)
def api_post_sensor_type_correlation(analysis_request: models.AnalysisRequestType):
    """
    Returns the list of stored datasets.
    """
    return services.serve_correlations(period=analysis_request.period, category=analysis_request.category, group_type=analysis_request.group_by)


@analysis_router.get('/relation/{period}/{sensor1}/{sensor2}')
def api_get_relations(period: models.AnalysisPeriodType, sensor1: str, sensor2: str):
    pass
