# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
import flask
import dash
from dash import dcc, html
import plotly.express as px
import dask.dataframe as dd
import pandas as pd

import analysis.config as cfg
import analysis.process.merging as merge_data
import analysis.process.analyze as analyze_data

def setup_layout(app):
    df_merged_data = merge_data.merge_from_database().to_dataframe(meta=analyze_data.get_metadata())
    print(df_merged_data.head(10, npartitions=cfg.get_config().dask_cluster.partitions))
    df = pd.DataFrame({
        "Fruit": ["Apples", "Oranges", "Bananas", "Apples", "Oranges", "Bananas"],
        "Amount": [4, 1, 2, 2, 4, 5],
        "City": ["SF", "SF", "SF", "Montreal", "Montreal", "Montreal"]
    })

    fig = px.bar(df, x="Fruit", y="Amount", color="City", barmode="group")
    
    app.layout = html.Div(children=[
        html.H1('Dashboard Feedback + Sensor Data'),
        dcc.Graph(
        id='example-graph',
        figure=fig
    )
    ])


# https://docs.dask.org/en/stable/futures.html
# Your local variables define what is active in Dask.
def setup_app(name: str, server: flask.Flask, url_base_pathname: str, dask_client):
    dashboard_app = dash.Dash(name=__name__, server=server, url_base_pathname=url_base_pathname)
    dashboard_app.dask_client = dask_client
    setup_layout(dashboard_app)
    return dashboard_app
