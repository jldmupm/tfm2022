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
from dashboard.lo_analysis import analysis_header, analysis_collapse

from dashboard.server import app, server
from dashboard import callbacks


content_merged_timeline_row = dbc.Row(
    [
        dbc.Col([
            dcc.Graph(id='graph_merged_data'),
        ], md=16)
    ]
)

content_more_graphs_row = dbc.Row(
    [
        dbc.Col(
            dcc.Graph(id='graph_merged_violin'), md=6
        ),
        dbc.Col(
            dcc.Graph(id='graph_merged_density_map'), md=6
        )
    ]
)

content_correlations_row = dbc.Row(
    [
        dbc.Col([
            html.Div(id='div_correlations'),
        ], md=16)
    ]
)

content = html.Div(
    [
        general_info_row,
        html.Hr(),
        html.H2('Analysis Dashboard for Sensors & Votes',
                style=TEXT_STYLE),
        html.Hr(),
        dcc.Loading(
            id='loading-siderbar',
            type='default',
            children=[sidebar]
        ),
        html.Hr(),
        content_merged_timeline_row,
        content_more_graphs_row,
        content_correlations_row,
        html.Hr(),
        analysis_header,
        analysis_collapse
    ],
    style=CONTENT_STYLE
)

app.layout = html.Div(
    [
        content,
        # dcc.Store stores the intermediate value
        dcc.Store(id='available_rooms'),
        dcc.Store(id='available_measures'),
        dcc.Store(id='available_dates'),
        dcc.Store(id='data_in_current-range'),
        dcc.Store(id='lr_models'),
        dcc.Store(id='correlations'),
        dcc.Store(id='current_timeline')
    ])

