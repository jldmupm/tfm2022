# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from datetime import datetime, timedelta
import dateparser
import flask
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

import analysis.dashboard.daterange as daterange

from analysis.api.services import get_min_date, get_max_date, get_service_sensor_data

flask_server = flask.Flask(__name__)
dash_app = dash.Dash(server=flask_server, url_base_pathname='/')

def setup_layout(app):
    print('setting_layout')
    min_date = get_min_date() - timedelta(days=30)
    max_date = get_max_date() + timedelta(days=30)

    app.layout = html.Div(children=[
        html.H1('Dashboard Feedback + Sensor Data'),
        dcc.Tabs(id="tabs-for-graphs", value='sensor-graph', children=[
            dcc.Tab(label='Sensor', value='sensor-graph'),
            dcc.Tab(label='Feedback', value='feedback-graph'),
            dcc.Tab(label='Merged Data', value='merged-graph'),
        ]),
        dcc.RangeSlider(
            id='year_slider',
            min = daterange.unixTimeMillis(min_date),
            max = daterange.unixTimeMillis(max_date),
            value = [daterange.unixTimeMillis(min_date),
                     daterange.unixTimeMillis(max_date)],
            marks=daterange.getMarks(min_date, max_date, 1)
        )
    ])

@dash_app.callback(Output('tabs-for-graphs', 'children'),
              Input('tabs-for-graphs', 'value'))
def render_tabs_content(tab):
    if tab == 'sensor-graph':
        print('SENSOR DATA')
        return html.Div([
            html.H3('Sensors'),
            dcc.Graph(
                figure={
                    'data': [{
                        'x': [1, 2, 3],
                        'y': [3, 1, 2],
                        'type': 'line'
                    }]
                }
            )
        ])
    elif tab == 'feedback-graph':
        return html.Div([
            html.H3('Tab content 2'),
            dcc.Graph(
                id='graph-2-tabs-dcc',
                figure={
                    'data': [{
                        'x': [1, 2, 3],
                        'y': [5, 10, 6],
                        'type': 'bar'
                    }]
                }
            )
        ])
    elif tab == 'merged-graph':
        return html.Div([
            html.H3('Tab content 3'),
            dcc.Graph(
                id='graph-3-tabs-dcc',
                figure={
                    'data': [{
                        'x': [11, 12, 13],
                        'y': [55, 100, 60],
                        'type': 'bar'
                    }]
                }
            )
        ])            

    
# https://docs.dask.org/en/stable/futures.html
# Your local variables define what is active in Dask.

def create_dash_app(dask_client):
    global dash_app

    dash_app.dask_client = dask_client

    setup_layout(dash_app)
    
    return flask_server
