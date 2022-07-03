# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Dict, List, Tuple, Union
from datetime import date, datetime

import dash
from dash import dcc, html, Input, Output
from dash.dash_table import DataTable
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from diskcache import Cache as DCache

import pandas as pd

import analysis.config as cfg
import analysis.process.fetcher as data_fetcher

pd.set_option('display.max_columns', None)

app = dash.Dash(url_base_pathname='/')
cache = DCache('./.cache')
app.config.suppress_callback_exceptions = True

timeout = 30*60
all_rooms = data_fetcher.all_rooms()

def load_data(start_date: date, end_date: date, measure='temperature', room=None, tg='1H') -> Dict[str, pd.DataFrame]:
    print('load_data')
    category = cfg.get_config().data.feedback.category
#    ddf_feedback = data_fetcher.get_feedback_timeline(start_date, end_date, category=category)
    ddf_sensors = data_fetcher.get_sensors_timeline(start_date, end_date, category='Ambiente', measure=measure, room=room, timegroup=tg)
    return {
 #       'feedbacks': ddf_feedback,
        'sensors': ddf_sensors
    }


app.layout = html.Div(children=[
    html.H1('Dashboard Feedback + Sensor Data'),
    dcc.Loading(id="ls-loading-1",
                children=[
                    dcc.DatePickerRange(
                        id='date-picker-range-dates',
                        min_date_allowed=date(2021, 1, 1),
                        max_date_allowed=date(2030, 12, 31),
                        initial_visible_month=datetime.utcnow().date(),
                        end_date=datetime.utcnow().date()),
                    dcc.RadioItems(options=['measure', 'sensor'])
                    dcc.RadioItems(options=['1H','1D','1M'], value='1H', id='radio-timegroup', inline=True),
                    dcc.Dropdown(
                        id='dropdown-rooms',
                        options=all_rooms,
                        value=all_rooms[0],
                        multi=False),
                    dcc.Dropdown(
                        id='dropdown-measure',
                        options=['temperature+humidity', *data_fetcher.all_measures()],
                        value=[data_fetcher.all_measures()[0]],
                        multi=False),
                    dcc.Graph(id='merged-data-graph'),
                ])
])


@app.callback(Output("merged-data-graph", "figure"),
              Input("date-picker-range-dates", "start_date"),
              Input("date-picker-range-dates", "end_date"),
              Input("dropdown-measure", "value"),
              Input("dropdown-rooms", "value"),
              Input("radio-timegroup", "value"))
def render_main_graph(start_date: str, end_date: str, measure: str, room: str, timegroup: str):
    print('render')
    if not(start_date and end_date and measure and room):
        return {}
    start_date_object = date.fromisoformat(start_date)
    end_date_object = date.fromisoformat(end_date)
    # set up plotly figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    if measure == 'temperature+humidity':
        measure = 'temperature'
        timeseries_humidity = load_data(start_date=start_date_object,
                                      end_date=end_date_object,
                                      measure='humidity',
                                      room=room,
                                      tg=timegroup)['sensors']
    timeseries = load_data(start_date=start_date_object,
                           end_date=end_date_object,
                           measure=measure,
                           room=room,
                           tg=timegroup)['sensors']
    print('render', type(timeseries), timeseries.shape, timeseries.columns)
    # add first bar trace at row = 1, col = 1
    fig.add_trace(go.Bar(x=timeseries['time'], y=timeseries['value'],
                         name=measure,
                         marker_color = 'green',
                         opacity=0.4,
                         marker_line_color='rgb(8,48,107)',
                         marker_line_width=2),
                  row = 1, col = 1,
                  secondary_y=True)

    # add first scatter trace at row = 1, col = 1
    fig.add_trace(go.Scatter(x=timeseries['time'], y=timeseries['value'], line=dict(color='red'), name=measure),
                  row = 1, col = 1,
                  secondary_y=False)
    if measure == 'temperature+humidity':
        fig.add_trace(go.Scatter(x=timeseries_humidity['time'], y=timeseries_humidity['value'], line=dict(color='blue'), name='humidity'),
                      row = 1, col = 1,
                      secondary_y=False)

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
    app.run_server(debug=True)
