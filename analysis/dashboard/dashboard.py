# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from datetime import datetime, timedelta
import flask
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

import analysis.dashboard.daterange as daterange

import analysis.api.services as service

flask_server = flask.Flask(__name__)
dash_app = dash.Dash(server=flask_server, url_base_pathname='/')

def setup_layout(app):
    print('setting_layout')
    min_date = service.get_min_date() - timedelta(days=30)
    max_date = service.get_max_date() + timedelta(days=30)
    
    app.layout = html.Div(children=[
        html.H1('Dashboard Feedback + Sensor Data'),
        dcc.Tabs(id="tabs-for-graphs", value='sensor-graph', children=[
            dcc.Tab(label='Sensor', value='sensor-graph'),
            dcc.Tab(label='Feedback', value='feedback-graph'),
            dcc.Tab(label='Merged Data', value='merged-graph'),
        ]),
        html.Div(id='tabs-content'),
        dcc.RangeSlider(
            id='year_slider',
            min = daterange.unixTimeMillis(min_date),
            max = daterange.unixTimeMillis(max_date),
            value = [daterange.unixTimeMillis(min_date),
                     daterange.unixTimeMillis(max_date)],
            marks=daterange.getMarks(min_date, max_date, 1)
        )
    ])

@dash_app.callback(Output('sensor-type-dropdown', "options"),
                   Input('sensor-node-dropdown', 'value'))
def update_sensor_type_options():
    print('update_sensor_type_options')
    sensor_data = service.get_df_sensor_data(dash_app.dask_client)
    sensor_options = sensor_data[sensor_data['custom_id'] == selected_node]['sensor'].unique().compute().tolist()
    return sensor_options
    
@dash_app.callback(Output("sensor-graph", "figure"),
                   Input('sensor-node-dropdown', 'value'),
                   Input('sensor-type-dropdown', 'value'))
def render_sensor_graph(selected_node, selected_sensor_type):
    print('render_sensor_graph')
    sensor_data = service.get_df_sensor_data(dash_app.dask_client)

    if selected_node is None:
        filter_by_sensor_type = sensor_data['sensor'] == selected_sensor_type
        sensor_data_filtered = sensor_data[filter_by_sensor_type]
    else:
        filter_by_sensor_id = (sensor_data['custom_id'] == selected_node) & (sensor_data['sensor'] == selected_sensor_type)
        sensor_data_filtered = sensor_data[filter_by_sensor_id]
        
    sensor_data_filtered = sensor_data_filtered.compute()
        
    return px.scatter(x=sensor_data_filtered['date'], y=sensor_data_filtered['value'], color=sensor_data_filtered['room'])


def render_sensor_tab():
    print('render_sensor_tab')
    df_sensor = service.get_df_sensor_data(app.dask_client)
    sensor_types = df_sensor['sensor'].unique().compute().tolist()
    sensor_nodes = df_sensor['custom_id'].unique().compute().tolist()

    return html.Div([
        html.H3('Sensors'),
        dcc.Dropdown(options=sensor_nodes + [None], value=None, id='sensor-node-dropdown'),
        dcc.Dropdown(options=sensor_types, value=sensor_types[0], id='sensor-type-dropdown'),
        dcc.Graph(id="sensor-graph", style={"width": "100%", "display": "inline-block"})
    ])
    
@dash_app.callback(Output('tabs-content', 'children'),
                   Input('tabs-for-graphs', 'value'))
def render_tabs_content(tab):
    print('render_tabs_content')
    if tab == 'sensor-graph':
        return render_sensor_tab()
    elif tab == 'feedback-graph':
        return html.Div([
            html.H3('Feedback'),
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
            html.H3('Merged Data'),
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

def setupo_merge_dash_with_flask_app(dask_client):
    print('setupo_merge_dash_with_flask_app')
    global dash_app

    dash_app.dask_client = dask_client

    setup_layout(dash_app)
    
    return flask_server
