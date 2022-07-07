# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import logging
from typing import Any, Dict, List, Tuple
from datetime import date, datetime

import dash
from dash import dcc, html, Input, Output
from dash.dash_table import DataTable
import dateparser

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import pandas as pd

import httpx

from cachier import cachier

from analysis.cache import cache_app_mongetter
import analysis.config as cfg
import analysis.process.fetcher as data_fetcher


pd.set_option('display.max_columns', None)


app = dash.Dash(url_base_pathname='/')
app.config.suppress_callback_exceptions = True

all_rooms = data_fetcher.sensorized_rooms() + data_fetcher.feedback_rooms()

vote_data_set = {'dt': [], 'measure': [], 'room': [], 'score_min':[], 'score_mean':[], 'score_max':[], 'score_std':[], 'score_count':[]}
sensor_data_set = {'dt': [], 'measure': [], 'class': [], 'value_min':[], 'value_mean':[], 'value_max':[], 'value_std':[], 'value_count':[]}
    
url_votes = cfg.get_api_url() + '/api/v1/feedback/timeline'
url_sensor = cfg.get_api_url() + '/api/v1/sensorization/timeline'

#@cachier(mongetter=cache_app_mongetter)
def load_sensor_data(start_date: str, end_date: str, measure=None, room=None, tg='1H') -> Dict[str, List[Any]]:

    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg}

    r_sensor = httpx.post(url_sensor, json=data_request, timeout=None)
#    r_votes = httpx.post(url_votes, json=data_request, timeout=None)
    if r_sensor.status_code in [200] and r_sensor.status_code in [200]:
        return r_sensor.json()
    else:
        return sensor_data_set
    

app.layout = html.Div(children=[
    html.H1('Dashboard Feedback + Sensor Data'),
    dcc.Loading(id="ls-loading-1",
                children=[
                    dcc.DatePickerRange(
                        id='date-picker-range-dates',
                        min_date_allowed=date(2021, 1, 1),
                        max_date_allowed=date(2030, 12, 31),
                        initial_visible_month=datetime.utcnow().date(),
                        end_date=datetime.utcnow().date()),
                    dcc.RadioItems(options=['measure', 'sensor']),
                    dcc.RadioItems(options=['1H','1D','1M'], value='1H', id='radio-timegroup'),
                    dcc.Dropdown(
                        id='dropdown-rooms',
                        options=all_rooms,
                        value=all_rooms,
                        multi=True),
                    dcc.Dropdown(
                        id='dropdown-measure',
                        options=data_fetcher.all_measures(),
                        value=data_fetcher.all_measures(),
                        multi=True),
                    dcc.Graph(id='merged-data-graph'),
                ])])



@app.callback(Output("merged-data-graph", "figure"),
              Input("date-picker-range-dates", "start_date"),
              Input("date-picker-range-dates", "end_date"),
              Input("dropdown-measure", "value"),
              Input("dropdown-rooms", "value"),
              Input("radio-timegroup", "value"))
def render_main_graph(start_date: str, end_date: str, measures: List[str], rooms: List[str], timegroup: str):
    logging.debug(f'render_main_graph: ({start_date=}, {end_date=}, {measures=}, {rooms=}, {timegroup=})')
    if not(start_date and end_date and measures and rooms):
        return {}
    room_to_query = None if len(rooms) > 1 else rooms[0]
    measure_to_query = None if len(measures) > 1 else measures[0]
    
    ts_sensors = load_sensor_data(start_date=start_date,
                                  end_date=end_date,
                                  measure=measure_to_query,
                                  room=room_to_query,
                                  tg=timegroup)
    df_sensors = pd.DataFrame(ts_sensors)
    df_filtered_sensors = df_sensors[df_sensors['measure'].isin(measures) & df_sensors['class'].isin(rooms)]
    df_filtered_votes = pd.DataFrame(vote_data_set)
    logging.debug(f'render_main_graph: {type(ts_sensors)=}, {ts_sensors.keys()=}')
    logging.debug(f'render_main_graph: {type(df_sensors)=}, {df_sensors.columns=}', {df_sensors.shape})

    # set up plotly figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # fig = px.line(df_filtered_sensors, x='dt', y='value_mean',
    #               color='measure', facet_row='class')
    # fig.update_layout(transition_duration=500)

    
    figures = [
            px.line(df_filtered_sensors),
            px.line(df_filtered_votes)
    ]
    
    for i, figure in enumerate(figures):
        for trace in range(len(figure["data"])):
            fig.append_trace(figure["data"][trace], row=i+1, col=1)
    
    return fig


# ***********************
#    DASHBOARD MAIN
# ***********************
if __name__ == '__main__':
    app.run_server(debug=True)
