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

@analysis_router.post('/analysis/')
def api_get_analysis(analysis_request: models.AnalysisRequestType):
    """
    Returns the list of stored datasets.
    """
    return services.get_periodic_analysis(period=analysis_request.period, category=analysis_request.category, group_type=analysis_request.group_by)
