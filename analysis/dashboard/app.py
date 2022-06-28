# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Dict, List, Tuple, Union
from datetime import  datetime

import dash
from dash import dcc, html, Input, Output
from dash.dash_table import DataTable
import plotly.express as px
from diskcache import Cache as DCache
import dask
from dask.distributed import Client
import dask.dataframe as dd
from dask.cache import Cache
import pandas as pd

import analysis.config as cfg
import analysis.dashboard.fetcher as data_fetcher
import analysis.process.analyze as an
import analysis.process.dmerge as dm

pd.set_option('display.max_columns', None)

app = dash.Dash(url_base_pathname='/')
cache = DCache('./.cache')
app.config.suppress_callback_exceptions = True

timeout = 30*60
all_rooms = data_fetcher.all_rooms()


def load_data() -> Dict[str, dd.DataFrame]:
    print('load_data')
    category = cfg.get_config().data.feedback.category
    ddf_feedback = data_fetcher.get_feedback_timeline(datetime(2022,5,1), datetime.utcnow(), category=category)
    ddf_sensors = data_fetcher.get_sensors_timeline(datetime(2022,5,1), datetime.utcnow(), category=category)
    print('load_data',type(ddf_feedback))
    print('load_data',type(ddf_sensors))
    return {
        'feedbacks': ddf_feedback,
        'sensors': ddf_sensors
    }


loaded_data = load_data()


app.layout = html.Div(children=[
    html.H1('Dashboard Feedback + Sensor Data'),
    dcc.Loading(id="ls-loading-1",
                children=[
                    dcc.RadioItems(options=['1H','1D','1M'], value='1H', id='radio-timegroup', inline=True),
                    dcc.Dropdown(
                        id='dropdown-rooms',
                        options=all_rooms,
                        value=all_rooms[0],
                        multi=False),
                    dcc.Dropdown(
                        id='dropdown-measure',
                        options=data_fetcher.all_measures(),
                        value=[data_fetcher.all_measures()[0]],
                        multi=False),
                    dcc.Graph(id='merged-data-graph'),
                ])
])


@app.callback(Output("merged-data-graph", "figure"),
              Input("dropdown-measure", "value"),
              Input("dropdown-rooms", "value"),
              Input("radio-timegroup", "value"))
def render_main_graph(measure: str, room: str, timegroup: str):
    print('render')
    if not(measure and room):
        return {}
    print('render',loaded_data['feedbacks'].columns)
    print('render',loaded_data['sensors'].columns)
    ddf = data_fetcher.filter_timeline(loaded_data['feedbacks'], measure=measure, room_field='room', rooms=room, m_field='reasonsString', m_filter="|".join(cfg.get_reasons_for_measure(measure)))
    dds = data_fetcher.filter_timeline(loaded_data['sensors'], measure=measure, room_field='class', rooms=room, m_field='sensor', m_filter="|".join(cfg.get_sensors_for_measure(measure)))
    # Grouper not implemented by Dask
    df = ddf.compute(scheduler='processes')
    dfg = df.groupby(pd.Grouper(key='date', freq=timegroup)).agg({'score': 'mean'}, meta={'score':float}).reset_index('date')
             
    fig = px.bar(dfg, x='date', y=['score'])
#    fig = px.line(dfg, x='date',y=['r_avg', 'r_min', 'r_max'], markers=True)
    return fig


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

    app.run_server(debug=True)
