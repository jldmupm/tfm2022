# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import List
from datetime import  datetime
import dash
from dash import dcc, html, Input, Output
import plotly.express as px
from flask_caching import Cache
from dask.distributed import Client, LocalCluster
import pandas as pd

import analysis.dashboard.fetcher as data_fetcher

app = dash.Dash(url_base_pathname='/')
cache = Cache(app.server, config={
    # try 'filesystem' if you don't want to setup redis
    "CACHE_TYPE": "SimpleCache",  # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 300
})
app.config.suppress_callback_exceptions = True
print('-------')
timeout = 30*60
all_rooms = data_fetcher.all_rooms()
app.layout = html.Div(children=[
    html.H1('Dashboard Feedback + Sensor Data'),
    dcc.Dropdown(
        id='dropdown-rooms',
        options=all_rooms,
        value=all_rooms,
        multi=False),
    dcc.Dropdown(
        id='dropdown-measure',
        options=data_fetcher.all_sensors(),
        value=[data_fetcher.all_sensors()[0]],
        multi=False),
    dcc.Loading(id="ls-loading-1",
                children=[
                    dcc.Graph(id='merged-data-graph'),
                ])
])
print('******')
@app.callback(Output("merged-data-graph", "figure"),
              Input("dropdown-measure", "value"),
              Input("dropdown-rooms", "value"))
@cache.memoize(timeout=timeout)  # in seconds
def render_main_graph(sensors: str, rooms: str):
    if not(sensors and rooms):
        return {}
    ddf = data_fetcher.get_data_timeline(datetime(2022,6,1), datetime.utcnow(), sensors, rooms)
    df = ddf.compute()
    fig = px.bar(data_frame=df,
                 x='score', 
                 y='r_avg')
    fig.update_layout(transition_duration=500)
    return fig
    
if __name__ == '__main__':
    print('* * * DASHBOARD * * *')
    # if cfg.get_config().cluster.scheduler in ['distributed']:
    #     print('configured as distributed cluster')
    #     custom_dask_client = Client(cfg.get_config().cluster.distributed)
    # else:
    #     print('configured as local cluster')
    #     #custom_dask_client = Client(LocalCluster("127.0.0.1:8787", dashboard_address="0.0.0.0:8687"))
    #     #custom_dask_client.cluster.scale(cfg.get_config().cluster.workers)
    # print(custom_dask_client)
    # cfg.set_cluster_client(custom_dask_client)

    app.run_server(debug=True)
