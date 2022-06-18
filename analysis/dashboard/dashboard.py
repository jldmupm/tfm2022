# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import dateparser
import flask
import dash
from dash import dcc, html, Input, Output
import plotly.express as px

from analysis.api.services import get_service_distributed_data, get_min_date, get_max_date
    
def setup_layout(app):

    min_date = get_min_date()
    max_date = get_max_date()

    app.layout = html.Div(children=[
        html.H1('Dashboard Feedback + Sensor Data'),
        dcc.Tabs(id="tabs-example-graph", value='sensor-graph', children=[
            dcc.Tab(label='Sensors', value='sensor-graph'),
            dcc.Tab(label='Feedbacks', value='feedback-graph'),
            dcc.Tab(label='Merged', value='merged-graph'),
        ]),
        html.Div([
            "Input: ",
            dcc.Input(id='my-input', value='initial value', type='text')
        ]),
        html.Br(),
        html.Div(id='my-output'),
    ])

    @app.callback(
        Output(component_id='my-output', component_property='children'),
        Input(component_id='my-input', component_property='value')
    )
    def _update_output_div(input_value):
        return f'Output: {input_value}'

# https://docs.dask.org/en/stable/futures.html
# Your local variables define what is active in Dask.
def setup_app(name: str, dask_client):
    aux_server = flask.Flask(__name__)
    dashboard_app = dash.Dash(name=name, title=name, server=aux_server)
    dashboard_app.dask_client = dask_client
    setup_layout(dashboard_app)
    print(type(dashboard_app), dashboard_app)
    return aux_server
