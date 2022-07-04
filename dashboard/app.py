# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Dict, List, Tuple, Union
from datetime import date, datetime

import dash
from dash import dcc, html, Input, Output
from dash.dash_table import DataTable
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

timeout = 30*60
all_rooms = data_fetcher.sensorized_rooms() + data_fetcher.feedback_rooms()

#@cachier(mongetter=cache_app_mongetter)
def load_data(start_date: str, end_date: str, measure='temperature', room=None, tg='1H') -> dict:
    print('load_data')
    url_votes = cfg.get_api_url() + '/api/v1/feedback/timeline'
    url_sensor = cfg.get_api_url() + '/api/v1/sensorization/timeline'
    print(url_votes)
    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg}
    print('JSON request', data_request)
    r = httpx.post(url_sensor, json=data_request, timeout=None)
    if r.status_code in [200]:
        print('load_data response', r.json())
        return r.json()
    else:
        print(f'{r.status_code}: {r.text}')
        return {}
    

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
                        value=all_rooms[0],
                        multi=False),
                    dcc.Dropdown(
                        id='dropdown-measure',
                        options=['temperature+humidity', *data_fetcher.all_measures()],
                        value=[data_fetcher.all_measures()[0]],
                        multi=False),
                    dcc.Graph(id='merged-data-graph'),
                ])])



@app.callback(Output("merged-data-graph", "figure"),
              Input("date-picker-range-dates", "start_date"),
              Input("date-picker-range-dates", "end_date"),
              Input("dropdown-measure", "value"),
              Input("dropdown-rooms", "value"),
              Input("radio-timegroup", "value"))
def render_main_graph(start_date: str, end_date: str, measure: str, room: str, timegroup: str):
    print('render')
    if not(start_date and end_date and measure and room):
        return {}
    start_date_object = date.fromisoformat(start_date)
    end_date_object = date.fromisoformat(end_date)
    # set up plotly figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    timeseries = load_data(start_date=start_date,
                           end_date=end_date,
                           measure=measure,
                           room=room,
                           tg=timegroup)
    print('render', timeseries)
    # add first bar trace at row = 1, col = 1
    # fig.add_trace(go.Bar(x=timeseries['dt'], y=timeseries['score_mean'],
    #                      name=measure,
    #                      marker_color = 'green',
    #                      opacity=0.4,
    #                      marker_line_color='rgb(8,48,107)',
    #                      marker_line_width=2),
    #               row = 1, col = 1,
    #               secondary_y=True)
    fig.add_trace(go.Bar(x=timeseries['dt'], y=timeseries['value_mean'],
                         name=measure,
                         marker_color = 'green',
                         opacity=0.4,
                         marker_line_color='rgb(8,48,107)',
                         marker_line_width=2),
                  row = 1, col = 1,
                  secondary_y=True)
    
    return fig


# ***********************
#    DASHBOARD MAIN
# ***********************
if __name__ == '__main__':
    app.run_server(debug=True)
