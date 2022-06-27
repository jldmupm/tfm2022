# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import List
from datetime import  datetime
import dash
from dash import dcc, html, Input, Output
from dash.dash_table import DataTable
import plotly.express as px
from diskcache import Cache
from dask.distributed import Client, LocalCluster
from dask.cache import Cache
import pandas as pd

import analysis.dashboard.fetcher as data_fetcher
import analysis.process.analyze as an
import analysis.process.dmerge as dm

pd.set_option('display.max_columns', None)

app = dash.Dash(url_base_pathname='/')
cache = Cache('./cache')
app.config.suppress_callback_exceptions = True

timeout = 30*60
all_rooms = data_fetcher.all_rooms()
app.layout = html.Div(children=[
    html.H1('Dashboard Feedback + Sensor Data'),
    dcc.RadioItems(options=['1D','1M'], value='1M', id='radio-timegroup', inline=True),
    dcc.Dropdown(
        id='dropdown-rooms',
        options=all_rooms,
        value=all_rooms,
        multi=True),
    dcc.Dropdown(
        id='dropdown-measure',
        options=data_fetcher.all_sensors(),
        value=[data_fetcher.all_sensors()[0]],
        multi=False),
    DataTable(
        id="data-table-view"
    ),
    dcc.Loading(id="ls-loading-1",
                children=[
                    dcc.Graph(id='merged-data-graph'),
                ])
])

@app.callback(Output("merged-data-graph", "figure"),
              Output("data-table-view", "columns"),
              Output("data-table-view", "data"),
              Input("dropdown-measure", "value"),
              Input("dropdown-rooms", "value"),
              Input("radio-timegroup", "value"))
def render_main_graph(sensors: str, rooms: List[str], timegroup: str):
    if not(sensors and rooms):
        return {}, dm.MergeVoteWithMeasuresAvailableFields,[]
    ddf = data_fetcher.filter_timeline(data_fetcher.get_timeline(datetime(2022,6,1), datetime.utcnow()), sensors, rooms)
    print('render1',type(ddf), len(ddf))
    df = ddf.compute()
    print(df.head())
    print(type(rooms), rooms)
    print('SHAPE', df.shape)
    df = df.groupby(pd.Grouper(key='date', freq=timegroup)).mean().reset_index('date')
    fig = px.line(df, x='date',y=['r_avg', 'r_min', 'r_max'], markers=True)
    return fig, [{"name": i, "id": i} for i in df.columns], df.to_dict("records")

# ***********************
#    DASHBOARD MAIN
# ***********************
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

    cache = Cache(2e9)  # Leverage two gigabytes of memory
    cache.register()

    min_date = an.get_min_from_mongo('time')
    max_date = an.get_max_from_mongo('time')
    dates = an.get_unique_from_mongo('time')
    ddates = set()
    for d in dates:
        ddates.add(d.date())
    print('min/max:', min_date, max_date, ddates)

    app.run_server(debug=True)
