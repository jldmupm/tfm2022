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
from starlette.requests import empty_receive

from analysis.cache import cache_app_mongetter
import analysis.config as cfg
import analysis.process.fetcher as data_fetcher


pd.set_option('display.max_columns', None)


app = dash.Dash(url_base_pathname='/')
app.config.suppress_callback_exceptions = True

all_rooms = data_fetcher.sensorized_rooms() + data_fetcher.feedback_rooms()


empty_merged_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min_sensor':[], 'value_mean_sensor':[], 'value_max_sensor':[], 'value_std_sensor':[], 'value_count_sensor':[], 'value_min_vote':[], 'value_mean_vote':[], 'value_max_vote':[], 'value_std_vote':[], 'value_count_vote':[]}


url_votes = cfg.get_api_url() + '/api/v1/feedback/timeline'
url_sensor = cfg.get_api_url() + '/api/v1/sensorization/timeline'
url_merged = cfg.get_api_url() + '/api/v1/merge/timeline'
    
    
@cachier(mongetter=cache_app_mongetter)
def retrieve_merged_data(start_date: str, end_date: str, measure=None, room=None, tg='1H') -> pd.DataFrame:
    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg}

    r_merged = httpx.post(url_merged, json=data_request, timeout=None)

    if r_merged.status_code in [200]:
        dfmerged = pd.DataFrame(r_merged.json())
    else:
        dfmerged = pd.DataFrame(empty_merged_data_set, columns=empty_merged_data_set.keys())
 
    print(dfmerged.columns, dfmerged.shape)
    dfmerged = dfmerged.fillna(value=0)

    #return dfmerged.to_dict(orient='list')
    return dfmerged
    
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
#                    dcc.RadioItems(options=['measure', 'sensor']),
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
    
    df_data = retrieve_merged_data(start_date=start_date,
                                   end_date=end_date,
                                   measure=measure_to_query,
                                   room=room_to_query,
                                   tg=timegroup)
    print(df_data.keys())
    df_data = df_data.sort_values(by='dt')
    if df_data.empty:
        return {}

    # set up plotly figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # fig = px.line(df_filtered_sensors, x='dt', y='value_mean',
    #               color='measure', facet_row='class')
    # fig.update_layout(transition_duration=500)

    for imeasure in measures:
        for iroom in rooms:
            measure_line = df_data[(df_data['measure'] == imeasure) & (df_data['room'] == iroom)]
            fig.add_trace(go.Line(x=measure_line['dt'], y=measure_line['value_mean_sensor'], name=f'{imeasure} ({iroom})'))
            fig.add_trace(go.Bar(x=measure_line['dt'], y=measure_line['value_mean_vote'], name=f'vote {imeasure} ({iroom})'), secondary_y=True)
    
    return fig


# ***********************
#    DASHBOARD MAIN
# ***********************
if __name__ == '__main__':
    app.run_server(debug=True)
