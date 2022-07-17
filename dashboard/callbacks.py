from typing import List
from datetime import datetime

from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go
from dash.exceptions import PreventUpdate
from dash import callback, dcc, html, Input, Output, State

import pandas as pd

from dashboard.app import app

from dashboard.apiaccess import get_all_rooms, get_all_measures, get_merged_data, get_date_range, get_lr_models

from analysis.process.analyze import logistic_regression_from_json

@app.callback(
    Output("collapse", "is_open"),
    [Input("toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("collapse_analysis", "is_open"),
    [Input("toggle_analysis", "n_clicks")],
    [State("collapse_analysis", "is_open")],
)
def toggle_collapse_analysis(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
    Output('card_text_rooms', 'children'),
    Output('card_text_measurements','children'),
    Output('card_text_dates', 'children'),
    Output('dropdown_rooms', 'options'),
    Output('dropdown_measures', 'options'),
    
    Input('available_rooms', 'data'),
    Input('available_measures', 'data'),
    Input('available_dates', 'data'),
    Input('date_picker_range_dates', 'end_date')
)
def fill_dropdown_rooms(all_rooms: List[str], all_measures: List[str], minmax_dates: List[datetime],  _):
    print('fill_dropdown_rooms')
    if all_rooms is None:
        raise PreventUpdate
    print(f'fill_dropdown_rooms {all_rooms}')
    return f'ROOMS: {len(all_rooms)}', f'MEASURES: {len(all_measures)}', f'FROM {minmax_dates[0]} TO {minmax_dates[1]}', all_rooms, all_measures

@callback(
    Output('available_rooms', 'data'),
    Output('available_measures', 'data'),
    Output('available_dates', 'data'),
    
    Input('submit_button', 'n_clicks')
)
def initialize(n_clicks: int):
    print(f'initialize {n_clicks}')
    if n_clicks:
        # prevent the None callbacks is important with the store component.
        # you don't want to update the store for nothing.
        raise PreventUpdate

    rooms = get_all_rooms()
    measures = get_all_measures()
    dates = get_date_range()
    
    return rooms, measures, dates


@callback(
    Output('current_timeline', 'data'),

    State('date_picker_range_dates', 'start_date'),
    State('date_picker_range_dates', 'end_date'),
    State('dropdown_measures', 'value'),
    State('dropdown_rooms', 'value'),
    State('radio_items_time_group', 'value'),
    Input('submit_button', 'n_clicks')
)
def get_merged_timeline(start: str, end: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks: int):
    if not n_clicks:
        raise PreventUpdate
    if not (start and  end and measures and rooms):
        raise PreventUpdate
    room_to_query = None if len(rooms) > 1 else rooms[0]
    measure_to_query = None if len(measures) > 1 else measures[0]
    json_data = get_merged_data(start_date=start,
                                end_date=end,
                                measure=measure_to_query,
                                room=room_to_query,
                                tg=timegroup)
    return json_data


@callback(
    Output('graph_merged_data', 'figure'),
    Output('graph_merged_violin', 'figure'),
    Output('graph_merged_density_map', 'figure'),
    
    Input('current_timeline', 'data'),
    Input('dropdown_measures', 'value'),
    Input('dropdown_rooms', 'value'),
    Input('radio_items_time_group', 'value')
)
def update_graph_merged(stored_data: dict, measures: List[str], rooms: List[str], timegroup: str):
    df_data = pd.DataFrame(stored_data)
    if df_data is None:
        raise PreventUpdate
    if df_data.empty:
        raise PreventUpdate
    df_data = df_data.sort_values(by='dt')
    # set up plotly figure
    make_subplots(specs=[[{"secondary_y": True}]])

    #
    # **************************************************************
    #

    data = []
    for imeasure in measures:
        for iroom in rooms:
            measure_line = df_data[(df_data['measure'] == imeasure) & (df_data['room'] == iroom)]
            data.append(go.Bar(x=measure_line['dt'], y=measure_line['value_mean_vote'], name=f'vote {imeasure} ({iroom})'))
            data.append(go.Scatter(x=measure_line['dt'], y=measure_line['value_mean_sensor'], name=f'{imeasure} ({iroom})', yaxis='y2'))        
    fig_merged_timeline = go.Figure(data = data)

    fig_merged_timeline.update_layout(
        title=f"measurements and scores means ({timegroup})",
        yaxis=dict(
            title="vote mean",
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4")),
        #create 2nd y axis
        yaxis2=dict(title="reading mean",
                    overlaying="y",
                    side="right"),
        legend_title='measure (room)'
    )

    #
    # **************************************************************
    #

    fig_relation_violin = make_subplots(specs=[[{"secondary_y": True}]])

    fig_relation_violin = px.violin(df_data, y="value_mean_vote", color="measure",
                                    title="voting scores",
                                    violinmode='overlay', # draw violins on top of each other
                                    # default violinmode is 'group' as in example above
                                    hover_data=df_data.columns)
    fig_relation_violin.update_layout(
        title="Voting Score by Measurement",
        yaxis=dict(
            title="voting score",
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4")),
    )


    #
    # **************************************************************
    #

    fig_density_heatmap = px.density_heatmap(df_data, x="measure", y="value_mean_vote", marginal_x="histogram", marginal_y="histogram", text_auto=True)

    fig_density_heatmap.update_layout(
        title="Voting Score by Measurement",
        yaxis=dict(
            title="voting score average",
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4")),
    )
    
    return fig_merged_timeline, fig_relation_violin, fig_density_heatmap


@callback(
    Output('lr_models', 'data'),
    
    State('current_timeline', 'data'),
    State('date_picker_range_dates', 'start_date'),
    State('date_picker_range_dates', 'end_date'),
    State('dropdown_measures', 'value'),
    State('dropdown_rooms', 'value'),
    State('radio_items_time_group', 'value'),    
    Input('toggle_analysis', 'n_clicks')
)
def update_models(stored_data: dict, ini: str, end: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks):
    print('update_models')
    if n_clicks is None:
        raise PreventUpdate
    room_to_query = None if len(rooms) > 1 else rooms[0]
    measure_to_query = None if len(measures) > 1 else measures[0]
    models = get_lr_models(start_date=ini, end_date=end, measure=measure_to_query, room=room_to_query, tg=timegroup)
    
    return models


@callback(
    Output('graph_lr_predict', 'figure'),
    
    State('current_timeline', 'data'),
    State('dropdown_measures', 'value'),
    State('dropdown_rooms', 'value'),
    State('radio_items_time_group', 'value'),
    Input('lr_models', 'data')
)
def update_graph_predict(stored_data: dict, measures: List[str], rooms: List[str], timegroup: str, lr_models: dict):
    print(f'update_graph_predict {lr_models=}')
    df_data = pd.DataFrame(stored_data)
    if df_data is None:
        raise PreventUpdate
    if df_data.empty:
        raise PreventUpdate
    df_data = df_data.sort_values(by='dt')
    #
    # **************************************************************
    #

    data = []
    for imeasure in measures:
        for iroom in rooms:
            measure_line = df_data[(df_data['measure'] == imeasure) & (df_data['room'] == iroom)]
            data.append(go.Bar(x=measure_line['dt'], y=measure_line['value_mean_vote'], name=f'vote {imeasure} ({iroom})'))
            data.append(go.Scatter(x=measure_line['dt'], y=measure_line['value_mean_sensor'], name=f'{imeasure} ({iroom})', yaxis='y2'))

    print(type(lr_models), lr_models)
    if lr_models:
        print('ENTRANDO', measures)
        measures_as_vars = pd.pivot_table(df_data, values='value_mean_sensor', columns='measure', index=['dt'])
        measures_as_vars = measures_as_vars.fillna(value=0)
        
        for imeasure in measures:
            if not lr_models['models'].get(imeasure, False):
                continue
            print('CALCULANDO',imeasure)
            lr = logistic_regression_from_json(lr_models['models'][imeasure]['model'])
            data.append(go.Scatter(x=measures_as_vars.index.get_level_values(0), y=lr.predict(measures_as_vars), yaxis='y2', name=f'predict {imeasure}'))
            
    fig_predict_timeline = go.Figure(data = data)

    fig_predict_timeline.update_layout(
        title=f"predictiond of scores by the  measurements  ({timegroup})",
        yaxis=dict(
            title="vote mean",
            titlefont=dict(color="#1f77b4"),
            tickfont=dict(color="#1f77b4")),
        #create 2nd y axis
        yaxis2=dict(title="reading mean",
                    overlaying="y",
                    side="right"),
        legend_title='measure (room)'
    )
    
    return fig_predict_timeline
    
# @app.callback(Output("merged-data-graph", "figure"),
#               Output("relation-graph", "figure"),
#               State("date-picker-range-dates", "start_date"),
#               State("date-picker-range-dates", "end_date"),
#               State("dropdown-measure", "value"),
#               State("dropdown-rooms", "value"),
#               State("radio-timegroup", "value"),
#               Input("submit-button", "n_clicks"))
# def render_timeline_and_violin_graph(start_date: str, end_date: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks: int):
#     logging.debug('render_timeline_and_violin_graph (ENTER)')
#     if not(start_date and end_date and measures and rooms and n_clicks):
#         return {}
#     room_to_query = None if len(rooms) > 1 else rooms[0]
#     measure_to_query = None if len(measures) > 1 else measures[0]
    
#     df_data = retrieve_merged_data(start_date=start_date,
#                                    end_date=end_date,
#                                    measure=measure_to_query,
#                                    room=room_to_query,
#                                    tg=timegroup)
#     df_data = df_data.sort_values(by='dt')
#     if df_data.empty:
#         return {}, {}

#     # set up plotly figure
#     make_subplots(specs=[[{"secondary_y": True}]])

#     # fig = px.line(df_filtered_sensors, x='dt', y='value_mean',
#     #               color='measure', facet_row='class')
#     # fig.update_layout(transition_duration=500)

#     data = []
#     for imeasure in measures:
#         for iroom in rooms:
#             measure_line = df_data[(df_data['measure'] == imeasure) & (df_data['room'] == iroom)]
#             data.append(go.Bar(x=measure_line['dt'], y=measure_line['value_mean_vote'], name=f'vote {imeasure} ({iroom})'))
#             data.append(go.Scatter(x=measure_line['dt'], y=measure_line['value_mean_sensor'], name=f'{imeasure} ({iroom})', yaxis='y2'))
#     measures_as_vars = None
#     if models:
#         measures_as_vars = pd.pivot_table(df_data, values='value_mean_sensor', columns='measure', index=['dt'])
#         measures_as_vars = measures_as_vars.fillna(value=0)
        
#         for imeasure in measures:
#             if not models.get(imeasure, False):
#                 continue
#             data.append(go.Scatter(x=measures_as_vars.index.get_level_values(0), y=models[imeasure].predict(measures_as_vars), yaxis='y2', name=f'predict {imeasure}'))
            
#     fig = go.Figure(data = data)

#     fig.update_layout(
#         title=f"measurements and scores means ({timegroup})",
#         yaxis=dict(
#             title="vote mean",
#             titlefont=dict(color="#1f77b4"),
#             tickfont=dict(color="#1f77b4")),
#         #create 2nd y axis
#         yaxis2=dict(title="reading mean",
#                     overlaying="y",
#                     side="right"),
#         legend_title='measure (room)'
#     )

#     fig_relation = make_subplots(specs=[[{"secondary_y": True}]])

#     fig_relation = px.violin(df_data, y="value_mean_vote", color="measure",
#                              title="voting scores",
#                              violinmode='overlay', # draw violins on top of each other
#                              # default violinmode is 'group' as in example above
#                              hover_data=df_data.columns)
#     fig.update_layout(
#         yaxis=dict(
#             title="voting score",
#             titlefont=dict(color="#1f77b4"),
#             tickfont=dict(color="#1f77b4")),
#     )
#     logging.debug('render_timeline_and_violin_graph (EXIT)')    
#     return fig, fig_relation


# @app.callback(
#     Output("regression-result-div", "children"),
#     State("date-picker-range-dates", "start_date"),
#     State("date-picker-range-dates", "end_date"),
#     State("dropdown-measure", "value"),
#     State("dropdown-rooms", "value"),
#     State("radio-timegroup", "value"),
#     Input("analisis-button", "n_clicks"))
# def render_analysis(start_date: str, end_date: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks: int):
#     logging.debug('render_analysis (ENTER)')
#     if not(start_date and end_date and measures and rooms and n_clicks):
#         return {}
#     room_to_query = None if len(rooms) > 1 else rooms[0]
#     measure_to_query = None if len(measures) > 1 else measures[0]
#     analisis_result = start_analisis(start_date=start_date,
#                                      end_date=end_date,
#                                      measure=measure_to_query,
#                                      room=room_to_query,
#                                      tg=timegroup)

#     if not analisis_result:
#         return {}, {}

#     res = Stack(
#         children=[
#             Stack(
#                 children=[
#                     html.H2(measure),
#                     *[html.Div(children=e) for e in [
#                         f"accuracy: {content['accuracy']}",
#                         f"mse: {content['mse']}",
#                     ]]
#                 ]) for measure, content in analisis_result['models'].items() ]
#     )
#     logging.debug('render_analysis (EXIT)')
#     return res
