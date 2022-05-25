# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import dash
from dash import dcc, html
import plotly.express as px
import dask.dataframe as dd

import src.process.analyze as analyze
import src.dask.setup_client

def init():
    src.dask.setup_client.setup()
