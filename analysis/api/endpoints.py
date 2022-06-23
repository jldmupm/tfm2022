from typing import List
from dask.dataframe.core import series_map
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

@analysis_router.get('/analysis/{period}')
def api_get_analysis(period: models.AnalysisPeriodType):
    """
    Returns the list of stored datasets.
    """
    return services.get_periodic_analysis(period)
