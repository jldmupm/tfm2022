from copy import deepcopy
from datetime import datetime

import pandas as pd

import analysis.config as cfg
import analysis.sensors.mg_source as mg
import analysis.feedback.models as fb_models
import analysis.process.dmerge as dm

import analysis.api.models as models


def serve_correlations(period: models.AnalysisPeriodType, category: models.AnalysisCategoriesType, group_type: mg.GROUP_SENSORS_USING_TYPE):
    """
    Serving the analysis.
    """
    # calculate the period
    (start_at, end_at) = period.get_period()

    merged = calculate_merged_data(start_at, end_at, category, group_type)
    # get all category values
    [posc, negc] = fb_models.CategoriesEnum.AMBIENTE.all_categories()
    # get all sensor types:
    sensors_query = merged[['sensor_type']].drop_duplicates()['sensor_type'].compute().tolist()

    correlations = []
    for sensor in sensors_query:

        for cat in posc:
            
    list(map(lambda s: {'sensor_type': s, 'correlations': merged[merged['sensor_type'] == s][['score','r_avg']].corr().compute().to_dict()}, sensors_query))


    result = list(map(lambda e: {'sensor_type': e['sensor_type'], 'correlation_score_avg': e['correlations']['score']['r_avg']}, correlations))
    
    return {
        'start': start_at,
        'end': end_at,
        'correlations': result
    }
