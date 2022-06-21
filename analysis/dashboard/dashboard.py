# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from datetime import datetime, timedelta
import flask
import dash
from dash import dcc, html, Input, Output
from pandas.core import groupby
import plotly.express as px

import analysis.dashboard.daterange as daterange

import analysis.api.services as service

dash_app = dash.Dash(url_base_pathname='/')

def setup_layout(app):
    min_date = service.get_min_date() - timedelta(days=30)
    max_date = service.get_max_date() + timedelta(days=30)
    unique_sensor_types = service.get_unique_sensor_types()
    
    app.layout = html.Div(children=[
        html.H1('Dashboard Feedback + Sensor Data'),
        dcc.Dropdown(unique_sensor_types, 'humidity', id='sensor-type-dropdown'),
        dcc.Graph(id='merged-data-graph'),
        dcc.RangeSlider(
            id='date-range-slider',
            min = daterange.unixTimeMillis(min_date),
            max = daterange.unixTimeMillis(max_date),
            value = [daterange.unixTimeMillis(min_date),
                     daterange.unixTimeMillis(max_date)],
            marks=daterange.getMarks(min_date, max_date, 1)
        )
    ])

@dash_app.callback(Output("merged-data-graph", "figure"),
                   Input('date-range-slider', 'value'),
                   Input('sensor-type-dropdown', 'value'))
def generate_figure_vote_and_sensor(date_range, sensor_type = 'humidity'):
    min_date = datetime.fromtimestamp(date_range[0])
    max_date = datetime.fromtimestamp(date_range[1])
    print(min_date, max_date)
    df_merged = service.get_df_sensor_type_vs_vote()
    print(df_merged.shape)
    print(df_merged.dtypes)
    print(sensor_type)
    print(df_merged)
    fig = px.bar(
        data_frame=df_merged.groupby(['score']).mean().reset_index(), 
        x="score", 
        y="sensor_avg"
    )
    print("*end*")
    return fig

#setup_layout(dash_app)
#dash_app.run(port='5050')
