# Run this app with `poetry run python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.
from typing import Any, Dict, List, Tuple
from datetime import date, datetime

import dash
from dash import dcc, html, Input, Output, State
from dash.dash_table import DataTable
import dateparser

import analysis.config as cfg

import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

import pandas as pd

import httpx

from cachier import cachier
from starlette.requests import empty_receive

from analysis.cache import cache_app_mongetter
import analysis.process.fetcher as data_fetcher


pd.set_option('display.max_columns', None)


app = dash.Dash(url_base_pathname='/',prevent_initial_callbacks=True)
app.config.suppress_callback_exceptions = True

all_rooms = data_fetcher.sensorized_rooms() + data_fetcher.feedback_rooms()


empty_merged_data_set = {'dt': [], 'measure': [], 'room': [], 'value_min_sensor':[], 'value_mean_sensor':[], 'value_max_sensor':[], 'value_std_sensor':[], 'value_count_sensor':[], 'value_min_vote':[], 'value_mean_vote':[], 'value_max_vote':[], 'value_std_vote':[], 'value_count_vote':[]}


url_votes = cfg.get_api_url() + '/api/v1/feedback/timeline'
url_sensor = cfg.get_api_url() + '/api/v1/sensorization/timeline'
url_merged = cfg.get_api_url() + '/api/v1/merge/timeline'
url_analisys = cfg.get_api_url() + '/api/v1/analysis/linear-regression'    
    
@cachier(mongetter=cache_app_mongetter)
def retrieve_merged_data(start_date: str, end_date: str, measure=None, room=None, tg='1H') -> pd.DataFrame:
    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg}

    r_merged = httpx.post(url_merged, json=data_request, timeout=None)

    if r_merged.status_code in [200]:
        dfmerged = pd.DataFrame(r_merged.json())
    else:
        dfmerged = pd.DataFrame(empty_merged_data_set, columns=empty_merged_data_set.keys())
 
    dfmerged = dfmerged.fillna(value=0)

    return dfmerged

@cachier(mongetter=cache_app_mongetter)
def start_analisis(start_date: str, end_date: str, measure=None, room=None, tg='2H') -> pd.DataFrame:
    data_request = {'ini_date': start_date, 'end_date': end_date, 'measure': measure, 'room': room, 'freq': tg, 'test_size': 0.3}
    r_analisis = httpx.post(url_analisys, json=data_request, timeout=None)

    if r_analisis.status_code in [200]:
        result = r_analisis.json()
    else:
        result = {}
    return result


def Stack(children, direction="column", **kwargs):
    return html.Div(children=children,
                    style={
                        'display': 'flex',
                        'flex-direction': direction,
                        'width': '100%'
                    })

app.layout = html.Div(children=[
    html.H1('Feedback and Sensor Data Dashboard'),
    dcc.Loading(id="ls-loading-1",
                children=[
                    Stack(children=[
                    dcc.DatePickerRange(
                        id='date-picker-range-dates',
                        min_date_allowed=date(2021, 1, 1),
                        max_date_allowed=date(2030, 12, 31),
                        initial_visible_month=datetime.utcnow().date(),
                        end_date=datetime.utcnow().date()),
#                    dcc.RadioItems(options=['measure', 'sensor']),
                    dcc.RadioItems(options=['1H','2H', '1W', '1D','1M'], value='2H', id='radio-timegroup'),
                    dcc.Dropdown(
                        id='dropdown-rooms',
                        options=all_rooms,
                        value=all_rooms,
                        multi=True),
                    dcc.Dropdown(
                        id='dropdown-measure',
                        options=data_fetcher.all_measures(),
                        value=data_fetcher.all_measures(),
                        multi=True),
                    html.Button(id='submit-button', n_clicks=0, children="Refresh"),
                    dcc.Graph(id='merged-data-graph'),
                    Stack(
                        direction='row',
                        children=[
                            Stack(children=[
                                html.Button(id="analisis-button", n_clicks=0, children="Analyze"),
                                html.Div(id="regression-result-div"),
                                dcc.Graph(id="main-components-graph"),
                                dcc.Graph(id='relation-graph')
                            ])])
                    ])
                ])])


@app.callback(Output("main-components-graph", "figure"),
              Output("regression-result-div", "children"),
              State("date-picker-range-dates", "start_date"),
              State("date-picker-range-dates", "end_date"),
              State("dropdown-measure", "value"),
              State("dropdown-rooms", "value"),
              State("radio-timegroup", "value"),
              Input("analisis-button", "n_clicks"))
def analyze_and_render(start_date: str, end_date: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks: int):
    if not(start_date and end_date and measures and rooms and n_clicks):
        return {}
    room_to_query = None if len(rooms) > 1 else rooms[0]
    measure_to_query = None if len(measures) > 1 else measures[0]    
    analisis_result = start_analisis(start_date=start_date,
                                     end_date=end_date,
                                     measure=measure_to_query,
                                     room=room_to_query,
                                     tg=timegroup)
    df_rlg = pd.DataFrame({
        'features': list(analisis_result['coefficients']['measure'].values()),
        'coeffs': list(analisis_result['coefficients']['0'].values())
        })
    fig_analisis = px.bar(df_rlg, x='features', y='coeffs')
    fig_analisis.update_xaxes(type='category')

    res = Stack(
        children=[
            html.Div(children=e) for e in [
                f"aquracy: {analisis_result['aquracy']}",
                f"mse: {analisis_result['mse']}",
                f"features: {', '.join(list(analisis_result['coefficients']['measure'].values()))}",
                f"coefficients:{', '.join(list(map(str,(analisis_result['coefficients']['0'].values()))))}",
                f"intercept: {', '.join(list(map(str,analisis_result['intercept'])))}"
            ]
        ]
    )
    
    return fig_analisis, res

@app.callback(Output("merged-data-graph", "figure"),
              Output("relation-graph", "figure"),
              State("date-picker-range-dates", "start_date"),
              State("date-picker-range-dates", "end_date"),
              State("dropdown-measure", "value"),
              State("dropdown-rooms", "value"),
              State("radio-timegroup", "value"),
              Input("submit-button", "n_clicks"))
def render_main_graph(start_date: str, end_date: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks: int):
    if not(start_date and end_date and measures and rooms and n_clicks):
        return {}
    room_to_query = None if len(rooms) > 1 else rooms[0]
    measure_to_query = None if len(measures) > 1 else measures[0]
    
    df_data = retrieve_merged_data(start_date=start_date,
                                   end_date=end_date,
                                   measure=measure_to_query,
                                   room=room_to_query,
                                   tg=timegroup)
    df_data = df_data.sort_values(by='dt')
    if df_data.empty:
        return {}

    # set up plotly figure
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # fig = px.line(df_filtered_sensors, x='dt', y='value_mean',
    #               color='measure', facet_row='class')
    # fig.update_layout(transition_duration=500)

    for imeasure in measures:
        for iroom in rooms:
            measure_line = df_data[(df_data['measure'] == imeasure) & (df_data['room'] == iroom)]
            fig.add_trace(go.Bar(x=measure_line['dt'], y=measure_line['value_mean_vote'], name=f'vote {imeasure} ({iroom})'), secondary_y=True)
            fig.add_trace(go.Line(x=measure_line['dt'], y=measure_line['value_mean_sensor'], name=f'{imeasure} ({iroom})'))

    fig.update_layout(
        title=f"measurements and scores means ({timegroup})",
        yaxis=dict(
            title="measure mean",
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4")),
        #create 2nd y axis
        yaxis2=dict(title="vote mean",
                    overlaying="y",
                    side="right",
                    position=0.15),
        legend_title='measure (room)'
    )

    fig_relation = make_subplots(specs=[[{"secondary_y": True}]])

    fig_relation = px.violin(df_data, y="value_mean_vote", color="measure",
                             title="voting scores",
                             violinmode='overlay', # draw violins on top of each other
                             # default violinmode is 'group' as in example above
                             hover_data=df_data.columns)
    fig.update_layout(
        yaxis=dict(
            title="voting score",
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4")),
    )
    
    return fig, fig_relation


# ***********************
#    DASHBOARD MAIN
# ***********************
if __name__ == '__main__':
    app.run_server(debug=True)
