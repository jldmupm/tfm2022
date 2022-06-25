from datetime import datetime

import pandas as pd
import dask.dataframe as dd

import analysis.config as cfg
import analysis.sensors.mg_source as mg
import analysis.process.dmerge as dm
import analysis.process.analyze as analyze_data

import analysis.api.models as models


def get_min_date():
    min_feedback = analyze_data.get_min_from_firebase('date').replace(tzinfo=None)
    min_sensor = analyze_data.get_min_from_mongo('time').replace(tzinfo=None)
    return max(min_feedback, min_sensor)


def get_max_date():
    max_feedback = analyze_data.get_max_from_firebase('date').replace(tzinfo=None)
    max_sensor = analyze_data.get_max_from_mongo('time').replace(tzinfo=None)
    return min(max_feedback, max_sensor)


def sensor_data_row_average(x, group_type = 'group_kind_type'):
    return mg.get_average_sensor_data(mg.get_mongodb_collection(),
                                      datetime.fromtimestamp(x['timestamp']),
                                      x['duration'],
                                      x['room'],
                                      group_type=group_type)


def serve_periodic_analysis(period: models.AnalysisPeriodType, category: models.AnalysisCategoriesType, group_type: mg.GROUP_SENSORS_USING_TYPE):
    """
    Serving the analysis.
    """
    # calculate the period
    (start_at, end_at) = period.get_period()

    # check if a file or firestore should be used to retrieve feedback data and load and filter it
    if cfg.fileForFeedback():
        print('From file...')
        ddf = dm.df_loader_from_file(cfg.fileForFeedback(), start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category)
    else:
        print('From Firestore...')
        ddf = dm.df_loader_from_firebase(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=category)
    # get the pairs that will be queried from the sensors database.
    groups_to_query = ddf[['timestamp', 'duration', 'room']].drop_duplicates()
    # query and store the sensors data
    groups_to_query['sensor_data'] = groups_to_query.apply(func=sensor_data_row_average, group_type=group_type, axis=1)
    # remove rows without sensor data
    groups_to_query = groups_to_query[groups_to_query['sensor_data'].str.len() > 0]
    # apply the queried sensor data to the feeback.
    ddf_merged = dd.merge(ddf, groups_to_query, how='right', left_on=['timestamp', 'duration', 'room'], right_on=['timestamp', 'duration', 'room'])
    ddf_exploded = ddf_merged.explode('sensor_data')
    ddf_exploded['sensor_data'] = ddf_exploded.apply('sensor_data', axis=1)
    pd.set_option('display.max_rows', 500)
    print(ddf_exploded.compute().at[1, 'sensor_data'])
#    ddf_full = ddf_exploded.map_partitions(lambda df: df.drop('sensor_data', axis=1).join(pd.DataFrame(df.sensor_data.values.tolist())), meta=dm.get_metadata())
    
    # result = ddf.compute().to_dict()
    # return {
    #     'initial_timestamp': start_at,
    #     'end_timestamp': end_at,
    #     **result,
    # }
    return { 'uno': list(range(-10,10))}
