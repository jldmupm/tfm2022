from copy import deepcopy
from datetime import datetime

import pandas as pd
import dask.dataframe as dd

import analysis.config as cfg
import analysis.sensors.mg_source as mg
import analysis.process.dmerge as dm
import analysis.process.analyze as analyze_data

import analysis.api.models as models


def sensor_data_row_average(x, group_type = 'group_kind_type'):
    return mg.get_average_sensor_data(mg.get_mongodb_collection(),
                                      datetime.fromtimestamp(x['timestamp']),
                                      x['duration'],
                                      x['room'],
                                      group_type=group_type)


def serve_correlations(period: models.AnalysisPeriodType, category: models.AnalysisCategoriesType, group_type: mg.GROUP_SENSORS_USING_TYPE):
    """
    Serving the analysis.
    """
    # calculate the period
    (start_at, end_at) = period.get_period()

    merged = calculate_merged_data(start_at, end_at, category, group_type)
    # get all sensor types:
    sensors_query = merged[['sensor_type']].drop_duplicates()['sensor_type'].compute().tolist()

    correlations = list(map(lambda s: {'sensor_type': s, 'correlations': merged[merged['sensor_type'] == s][['score','r_avg']].corr().compute().to_dict()}, sensors_query))


    result = list(map(lambda e: {'sensor_type': e['sensor_type'], 'correlation_score_avg': e['correlations']['score']['r_avg']}, correlations))
    
    return {
        'start': start_at,
        'end': end_at,
        'correlations': result
    }


def calculate_merged_data(start_at, end_at, category: models.AnalysisCategoriesType, group_type: mg.GROUP_SENSORS_USING_TYPE) -> dd.DataFrame:
    """
    Serving the merged data.
    """
    # check if a file or firestore should be used to retrieve feedback data and load and filter it
    if cfg.fileForFeedback():
        print('From file...')
        ddf = dm.df_loader_from_file(cfg.fileForFeedback(), start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category)
    else:
        print('From Firestore...')
        ddf = dm.df_loader_from_firebase(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category)
    ddf = ddf.drop(labels=['id', 'type'], axis=1)
    # get the pairs that will be queried from the sensors database.
    groups_to_query = ddf[['timestamp', 'duration', 'room']].drop_duplicates()
    # query and store the sensors data
    groups_to_query['sensor_data'] = groups_to_query.apply(func=sensor_data_row_average, group_type=group_type, axis=1)
    # remove rows without sensor data
    groups_to_query = groups_to_query[groups_to_query['sensor_data'].str.len() > 0]
    # apply the queried sensor data to the feeback.
    ddf_merged = dd.merge(ddf, groups_to_query, how='right', left_on=['timestamp', 'duration', 'room'], right_on=['timestamp', 'duration', 'room'])
    # remove votes without sensor data
    ddf_merged = ddf_merged[ddf_merged['sensor_data'].str.len() > 0]
    ddf_exploded = ddf_merged.explode('sensor_data')
    ddf_exploded['sensor_data'] = ddf_exploded.apply('sensor_data', axis=1, meta=('sensor_data', 'object'))
    ddf_full = ddf_exploded.map_partitions(lambda df: df.drop('sensor_data', axis=1).join(pd.DataFrame(df.sensor_data.values.tolist())), meta=dm.get_metadata())

    return ddf_full
