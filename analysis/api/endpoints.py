import fastapi
from fastapi.param_functions import Depends
import analysis.config as cfg

from analysis.api.services import get_min_date, get_max_date, get_df_merged_data

analysis_router = fastapi.APIRouter()

@analysis_router.get('/version')
def api_get_version():
    return {
        'major': 0,
        'middle': 1,
        'minor': 0
    }

@analysis_router.get('/analysis')
def api_get_analysis(dask_client = Depends(cfg.get_dask_client)):
    return {
        'min_date': get_min_date(),
        'max_date': get_max_date(),
        'size': get_df_merged_data(dask_client).compute().shape
    }
