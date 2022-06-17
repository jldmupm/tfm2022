# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import flask
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd

import analysis.process.merging as merge_data
import analysis.process.analyze as analyze_data

def get_data():
    global df_data_feedback
    global df_data_analysis
    
    pd.set_option('display.max_columns', None)
    df_data_feedback = analyze_data.get_feedback_flattend_dask_dataframe(merge_data.bag_loader_from_file('./all_feedbacks.csv', category='Ambiente'))
    df_data_analysis = analyze_data.get_merged_dask_dataframe(merge_data.merge_from_file('./all_feedbacks.csv'))

    res = {
        'feedback': df_data_feedback,
        'sensor': None,
        'analysis': df_data_analysis
    }
    
    return res
    
def setup_layout(app):
    df_feedback = get_data()['feedback'].compute()
    
    fig = px.box(df_feedback, x="category", y="score", color="room")
    fig.update_traces(quartilemethod="exclusive") # or "inclusive", or "linear" by default

    app.layout = html.Div(children=[
        html.H1('Dashboard Feedback + Sensor Data'),
        dcc.Graph(
            id='example-graph',
            figure=fig
        ),
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
def setup_app(name: str, server: flask.Flask, url_base_pathname: str, dask_client):
    dashboard_app = dash.Dash(name=name, title=name, server=server, url_base_pathname=url_base_pathname)
    dashboard_app.dask_client = dask_client
    get_data()
    setup_layout(dashboard_app)
    return dashboard_app
