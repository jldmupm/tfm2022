"""
Retrieves the data needed by the frontend services.
"""
from datetime import date, datetime, timedelta

from typing import List, Optional, Tuple

import dateparser

from pandas.io.formats.format import Timedelta64Formatter
from sklearn.utils.validation import joblib

import analysis.config as cfg

import pandas as pd

from cachier import cachier
from analysis.cache import cache_app_mongetter

import analysis.feedback.fb_source as fb
import analysis.sensors.mg_source as mg
import analysis.process.analyze as an

from joblib import Parallel, delayed

feedback_columns = {'subjectId': 'object',
                    'duration': 'int16',
                    'room': 'object',
                    'date': 'object',
                    'reasonsString': 'object',
                    'score': 'int16',
                    'reasonsList': 'object',
                    'category': 'object',
                    'measure': 'object'
                    }
feedback_end_columns = {'subjectId': 'object',
                        'duration': 'int16',
                        'room': 'object',
                        'date': 'object',
                        'reasonsString': 'object',
                        'score': 'int16',
                        'reasonsList': 'object',
                        'category': 'object',
                        'measure': 'object',
                        'dt': 'object'
                    }

sensor_raw_columns = {
    '_id': 'object',
    'time': 'object',
    'data': 'object',
    'class': 'object',
    'hub': 'object',
    'node': 'object',
    'id': 'object',
}

sensor_end_columns = {
    '_id': 'object',
    'time': 'object',
    'data': 'object',
    'class': 'object',
    'hub': 'object',
    'node': 'object',
    'id': 'object',
    'measure': 'object',
    'sensor': 'object',
    'value': 'float',
    'dt': 'object'
}

# TODO: distributed calculate feedback & sensors: read from a single day and concat results.

def divide_range_in_days(ini: datetime, end: datetime) -> List[Tuple[datetime, datetime]]:
    days = []
    iter_datetime: datetime = ini
    while (iter_datetime < end):
        ini_datetime = iter_datetime.replace(hour=0, minute=0, second=0, microsecond=0)
        end_datetime = iter_datetime.replace(hour=23, minute=59, second=59, microsecond=999999)
        days.append((ini_datetime, end_datetime))
        iter_datetime = iter_datetime + timedelta(days=1)
    return days

@cachier(mongetter=cache_app_mongetter)
def calculate_sensors_aux(ini_datetime: datetime, end_datetime: datetime, category: str, measures: Optional[List[str]] = None, rooms: Optional[List[str]] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> pd.DataFrame:
    cursor = mg.mongo_sensor_reading(min_datetime=ini_datetime, max_datetime=end_datetime, rooms=rooms, sensor_types=cfg.get_sensor_list_for_measures(measures))
    dfcursor = pd.DataFrame(cursor)#, columns=sensor_raw_columns.keys())
    # from my own:
    if dfcursor.empty:
        return pd.DataFrame({k: [] for k in sensor_end_columns.keys()})
    dfcursor['new_vals'] = dfcursor.apply(lambda x: [{'sensor':k, 'value': v} for k, v in x['data'].items()], axis=1)
    temp1 = dfcursor.explode('new_vals')
    result = pd.concat([temp1, temp1['new_vals'].apply(pd.Series)], axis=1)
    
    result.drop(columns=['new_vals', 'data'], axis=1, inplace=True)
    result.dropna(axis=0)
    
    result.reset_index()
    
    result['measure'] = result.apply(lambda row: cfg.get_measure_list_from_sensor(row['sensor']), axis=1)
    result['dt'] = pd.to_datetime(result['time'])
    
    return result


def calculate_sensors(ini_datetime: datetime, end_datetime: datetime, category: str, measures: Optional[List[str]] = None, rooms: Optional[List[str]] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> pd.DataFrame:

    date_today = datetime.now().date()
    
    dataframes = []
    with joblib.parallel_backend('dask'):
        pjobs = joblib.Parallel(n_jobs=cfg.get_config().cluster.workers)
        dataframes = pjobs(delayed(calculate_sensors_aux)(ini_datetime=ini, end_datetime=end, category=category, measures=measures, rooms=rooms, group_type=group_type, ignore_cache=end.date() == date_today) for (ini, end) in divide_range_in_days(ini_datetime, end_datetime))
    df_res = pd.concat(dataframes)
    if df_res.empty:
        return pd.DataFrame({k: [] for k in sensor_end_columns.keys()})
    return df_res

    
@cachier(mongetter=cache_app_mongetter)
def calculate_feedback_aux(ini_datetime: datetime, end_datetime: datetime, category: str, measures: Optional[List[str]] = None, rooms: Optional[List[str]] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor', data_config=cfg.get_data_config()) -> pd.DataFrame:
    mockData = cfg.fileForFeedback()
    if mockData:
        feedback_from_file = pd.read_csv(mockData)
        feedback_from_file['dt'] = pd.to_datetime(feedback_from_file['date'])
        feedback_from_file['dt'] = feedback_from_file['dt'].dt.tz_localize(None)
        # filter dates:
        feedback_from_file = feedback_from_file[(feedback_from_file['dt'] >= ini_datetime) & (feedback_from_file['dt'] <= end_datetime)]
        # filter measures and rooms:
        if measures:
            feedback_from_file = feedback_from_file[(feedback_from_file['measure'].isin(measures))]
        if rooms:
            feedback_from_file = feedback_from_file[(feedback_from_file['room'].isin(rooms))]

        return feedback_from_file
    
    custom_generator = fb.firebase_feedback_reading(start_date=ini_datetime, end_date=end_datetime, measures=measures, category=category, rooms=rooms)
    dfstream = pd.DataFrame(custom_generator)

    if dfstream.empty:
        df = pd.DataFrame({k: [] for k in feedback_end_columns.keys()})
        return df

    # temp1 = dfstream.explode('votingTuple')
    # result = pd.concat([temp1, temp1['votingTuple'].apply(pd.Series)], axis=1)
    # result.drop('votingTuple', axis=1, inplace=True)
    # result.dropna(axis=0)
    result = dfstream
    
    result['dt'] = pd.to_datetime(dfstream['date'])
    result['measure'] = result['reasonsList'].map(cfg.get_measure_list_from_reasons)
    result = result.explode('measure')

    result.reset_index()

    return result

def calculate_feedback(ini_datetime: datetime, end_datetime: datetime, category: str, measures: Optional[List[str]] = None, rooms: Optional[List[str]] = None, group_type: mg.GROUP_SENSORS_USING_TYPE = 'group_kind_sensor') -> pd.DataFrame:

    current_date = datetime.now().date()
    disable_cache = not cfg.is_cache_enabled()
    pjobs = Parallel(n_jobs=cfg.get_config().cluster.workers)
    dataframes = pjobs([delayed(calculate_feedback_aux)(
        ini_datetime=ini,
        end_datetime=end,
        category=category,
        measures=measures,
        rooms=rooms,
        group_type=group_type,
        ignore_cache=(end.date() == current_date or disable_cache)
    ) for (ini, end) in divide_range_in_days(ini_datetime, end_datetime)])

    df_res = pd.concat(dataframes).sort_values(by=['dt'])

    return df_res


def filter_data(ddf: pd.DataFrame, measures: Optional[List[str]] = None, room_field: Optional[str] = None, rooms: Optional[List[str]] = None, field: Optional[str] = None, value: Optional[str] = None, filter_error: Optional[str] = None) -> pd.DataFrame:
    
    query_params = { }
    # if field and value:
    #     query_params = {**query_params, field: value}
    if room_field and rooms:
        query_params = {**query_params, room_field: rooms}
    if measures:
        query_params = {**query_params, 'measure': measures}
    query_rest = ' & '.join([' (`{}` in "{}") '.format(k, v) for k, v in query_params.items()])
    # filter out errors
    query = query_rest
    if (len(query_rest) > 0) and filter_error and (len(filter_error) > 0):
        query += ' & '
    if filter_error and (len(filter_error) > 0):
        query += filter_error
    if len(query) > 0:
        result = ddf.query(query)
    else:
        result = ddf
    return result


def complete_timeseries(df: pd.DataFrame, freq: str, time_field: str, room_field: str):
    """
    (period, measure, room*): [value_min*, value_mean*, value_max*, value_std*, value_count*]

    Fill the dataframe with missing dates, measures and rooms with the average of the measure, room.

    NOTE: it can be add Nan if no measure, room data is found.
    """
    if df.empty:
        return df
    # calculate missing values as mean
    min_date = df.index.get_level_values(0).min()
    max_date = df.index.get_level_values(0).max()
    unique_measures = df.index.get_level_values(1).unique()
    unique_rooms = df.index.get_level_values(2).unique()
    list_dates = pd.date_range(start=min_date, freq=freq, end=max_date)
    multiindex = pd.MultiIndex.from_product([list_dates, unique_measures, unique_rooms], names=['period', 'measure', room_field])
    all_dates_df = pd.DataFrame(index=multiindex, columns=[])
    means_df = df.groupby(['measure', room_field]).mean()
    all_dates_df = all_dates_df.reset_index(0)
    all_dates_with_data_df = (all_dates_df
                              .join(means_df)
                              .set_index('period', append=True)
                              .reorder_levels(['period', 'measure', room_field]))

    idx_has_no_real_data = all_dates_with_data_df.index.difference(df.index)

    res = pd.concat([df, all_dates_with_data_df.loc[idx_has_no_real_data]])
    res = res.reset_index()
    return res


def build_timeseries(data: pd.DataFrame, ini_datetime: datetime, end_datetime: datetime, time_field: str, freq: str, agg_field_value: str, room_field: str, fill_value:float = 0.0) -> pd.DataFrame:
    aggregations = {agg_field_value + '_' + v: ( agg_field_value, v ) for v in ['min', 'mean', 'max', 'std', 'count']}

    new_column_names = {**{field_name: field_name.replace(agg_field_value, 'value') for field_name in aggregations.keys()},
                        room_field: 'room',
                        'period': 'dt'}

    data['period'] = pd.to_datetime(data[time_field]).dt.tz_localize(None)

    data = data.explode('measure')
    data.reset_index()
    
    grouped_by_period = data.groupby([pd.Grouper(key='period', axis=0, freq=freq, sort=True), pd.Grouper(key='measure'), pd.Grouper(key=room_field)]).agg(**aggregations).apply(lambda x: x.fillna(x.mean()))
    completed_data = complete_timeseries(grouped_by_period, freq=freq, room_field=room_field, time_field=time_field)
    
    completed_data = completed_data.rename(columns=new_column_names)
    completed_data = completed_data.fillna(value=fill_value)

    return completed_data


def all_measures():
    return [item for item in cfg.get_config().data.sensors.keys()]


def reasons_for_sensor(sensor: str) -> dict:
    return cfg.get_config().data.feedback.sense[sensor]


def sensor_type_for_sensor(sensor: str) -> List[str]:
    return cfg.get_config().data.sensors[sensor]


def sensorized_rooms():
    sensor_rooms = an.get_unique_from_mongo('class')
    return sensor_rooms


def feedback_rooms():
    mockData = cfg.fileForFeedback()
    if mockData:
        feedback_rooms_df: pd.DataFrame = pd.read_csv(mockData)
        feedback_rooms = feedback_rooms_df['room'].unique().tolist()
    else:
        feedback_rooms = [room for room in fb.get_rooms() if room]
       
    return feedback_rooms

def get_feedback_date_range():
    mockData = cfg.fileForFeedback()
    if mockData:
        feedback_rooms_df: pd.DataFrame = pd.read_csv(mockData)
        feedback_min_date = feedback_rooms_df['date'].min()
        feedback_max_date = feedback_rooms_df['date'].max()
    else:
        feedback_min_date = fb.get_min_date()
        feedback_max_date = fb.get_max_date()
    result = [dateparser.parse(d).replace(tzinfo=None) for d in [feedback_min_date, feedback_max_date]]
    return result


def get_sensor_date_range():
    sensor_min_date = mg.get_min_date()
    sensor_max_date = mg.get_max_date()
    return [sensor_min_date, sensor_max_date]


def get_date_range():
    feedback_range = get_feedback_date_range()
    sensor_range = get_sensor_date_range()
    return [min(feedback_range[0], sensor_range[0]),
            max(feedback_range[1], sensor_range[1])]
