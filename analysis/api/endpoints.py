import fastapi
from fastapi.param_functions import Depends
import analysis.config as cfg

from analysis.api.models import AnalysisResultType
from analysis.api.services import get_min_date, get_max_date, get_df_merged_data

analysis_router = fastapi.APIRouter()

def get_merged_data(dask_client = Depends(cfg.get_dask_client)):
    return get_df_merged_data(dask_client)

@analysis_router.get('/version', response_model=str)
def api_get_version():
    """
    Returns the version of the Analysis System.
    """
    return cfg.get_version()

@analysis_router.get('/analysis')
def api_get_analysis(merged_data = Depends(get_merged_data)):
    """
    Returns the results of analyze the merging of the Sensor and the CrowdSensing Information.
    """

    df = merged_data.compute()
    correlations = df[['sensor_type','category','sensor_avg','sensor_max','sensor_min','score','room','subjectId', 'reasonsString']].groupby('sensor_type').corr()
    return {
        'min_date': get_min_date(),
        'max_date': get_max_date(),
        'shape': correlations['score'].to_dict(),
    }
