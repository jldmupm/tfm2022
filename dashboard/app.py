# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Any, Dict, List, Tuple
from datetime import date, datetime

from dash import dcc, html
import dash_bootstrap_components as dbc
from dash.dash_table import DataTable

from sklearn.linear_model import LogisticRegression

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go


from dashboard.styles import CONTENT_STYLE, TEXT_STYLE
from dashboard.lo_general_info import general_info_row
from dashboard.lo_sidebar import sidebar

from dashboard.server import app, server
from dashboard import callbacks

content_second_row = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id='graph_1'), md=4
        ),
        dbc.Col(
            dcc.Graph(id='graph_2'), md=4
        ),
        dbc.Col(
            dcc.Graph(id='graph_3'), md=4
        )
    ]
)

content = html.Div(
    [
        html.H2('Analysis Dashboard for Sensors & Votes',
                style=TEXT_STYLE),
        html.Hr(),
        dcc.Loading(
            id='loading-siderbar',
            type='default',
            children=[sidebar]
        ),
        html.Hr(),
        general_info_row
    ],
    style=CONTENT_STYLE
)

app.layout = html.Div(
    [content,
     # dcc.Store stores the intermediate value
     dcc.Store(id='available_rooms'),
     dcc.Store(id='available_measures'),
     dcc.Store(id='data_in_current-range'),
     dcc.Store(id='lr_model'),
     dcc.Store(id='current_timeline')])


# def Stack(children, direction="column", **kwargs):
#     return html.Div(children=children,
#                     style={
#                         'display': 'flex',
#                         'flex-direction': direction,
#                         'width': '100%'
#                     })

# app.layout = html.Div(children=[
#     html.H1('Feedback and Sensor Data Dashboard'),
#     dcc.Loading(id="ls-loading-1",
#                 children=[
#                     Stack(children=[
#                         dcc.DatePickerRange(
#                             id='date-picker-range-dates',
#                             min_date_allowed=date(2021, 1, 1),
#                             max_date_allowed=date(2030, 12, 31),
#                             initial_visible_month=datetime.utcnow().date(),
#                             end_date=datetime.utcnow().date()),
#                         #                    dcc.RadioItems(options=['measure', 'sensor']),
#                         dcc.RadioItems(options=['1H','1D','1M'], value='1H', id='radio-timegroup'),
#                         dcc.Dropdown(
#                             id='dropdown-rooms',
#                             options=all_rooms,
#                             value=all_rooms,
#                             multi=True),
#                         dcc.Dropdown(
#                             id='dropdown-measure',
#                             options=data_fetcher.all_measures(),
#                             value=data_fetcher.all_measures(),
#                             multi=True),
#                         html.Button(id='submit-button', n_clicks=0, children="Refresh"),
#                         dcc.Graph(id='merged-data-graph'),
#                         dcc.Graph(id='relation-graph'),
#                         Stack(
#                             direction='row',
#                             children=[
#                                 Stack(children=[
#                                     html.Button(id="analisis-button", n_clicks=0, children="Analyze"),
#                                     html.Div(id="regression-result-div")
#                                     #                                dcc.Graph(id="main-components-graph"),
#                                 ])])
#                     ])
#                 ])])

