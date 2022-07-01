from typing import List
from copy import deepcopy
from datetime import datetime

import analysis.config as cfg

import pandas as pd
if cfg.get_config().cluster.scheduler_type in ['distributed']:
    import modin.pandas as pd
    
import api.models

import analysis.process.fetcher as fetcher

async def get_feedback(request: api.models.FeedbackRequest) -> pd.DataFrame:
#    async with Client(cfg.get_cluster(), asynchronous=True) as client:
    ini_datetime = datetime.combine(request.date, datetime.min.time())
    end_datetime = datetime.combine(request.date, datetime.max.time())
    df = fetcher.calculate_feedback(ini_datetime, end_datetime, 'Ambiente')
    return df
    
# def serve_correlations(period: api.models.AnalysisPeriodType, category: api.models.AnalysisCategoriesType, group_type: mg.GROUP_SENSORS_USING_TYPE):
#     """
#     Serving the analysis.
#     """
#     # calculate the period
#     (start_at, end_at) = period.get_period()

    # merged = calculate_merged_data(start_at, end_at, category, group_type)
    # # get all category values
    # [posc, negc] = fb_api.models.CategoriesEnum.AMBIENTE.all_categories()
    # # get all sensor types:
    # sensors_query = merged[['sensor_type']].drop_duplicates()['sensor_type'].compute().tolist()

    # correlations = []
    # for sensor in sensors_query:

    #     for cat in posc:
            
    # list(map(lambda s: {'sensor_type': s, 'correlations': merged[merged['sensor_type'] == s][['score','r_avg']].corr().compute().to_dict()}, sensors_query))


    # result = list(map(lambda e: {'sensor_type': e['sensor_type'], 'correlation_score_avg': e['correlations']['score']['r_avg']}, correlations))
    
    # return {
    #     'start': start_at,
    #     'end': end_at,
    #     'correlations': result
    # }
#    pass
