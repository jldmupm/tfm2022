from typing import List
import re

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

def get_periodic_analysis(period: models.AnalysisPeriodType, categories: List[models.AnalysisCategoriesType], group_type: mg.GROUP_SENSORS_USING_TYPE):
    (start_at, end_at) = period.get_period()

    if cfg.fileForFeedback():
        print('From file...')
        ddf = dm.df_loader_from_file(cfg.fileForFeedback(), start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category=list(map(lambda c: c.value, categories)))
    else:
        print('From Firestore')
        ddf = dm.df_loader_from_firebase(start_timestamp=start_at.timestamp(), end_timestamp=end_at.timestamp(), category="Estado físico")
    print(f"""

    GET_PERIODIC_ANALYSIS {ddf.compute().shape}

    """)
    ddf_merged = dm.add_extended_feedback_df_with_sensor_data(df=ddf, group_by=group_type)
    ddfc = ddf_merged.compute()
    result = ddfc.to_dict()
    return {
        'initial_timestamp': start_at,
        'end_timestamp': end_at,
        **result,
    }
