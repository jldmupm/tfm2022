import fastapi
from fastapi.param_functions import Depends

import analysis.config as cfg
import api.models
import api.services as services

analysis_router = fastapi.APIRouter()

@analysis_router.get('/version', response_model=str)
async def api_get_version():
    """
    Returns the version of the Analysis System.
    """
    return cfg.get_version()


@analysis_router.get('/configuration', response_model=api.models.ConfigResponse)
async def api_get_configuration():
    return cfg.get_config()


@analysis_router.post('/feedback/', response_model=api.models.FeedbackResponse)
async def api_get_feedback(result=Depends(services.get_feedback)):
    """
    Returns the queried feedback
    """
    response = result.to_dict(orient='list')
    print([type(e) for e in response['subjectId']])
    return response
    
