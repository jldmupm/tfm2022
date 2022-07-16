from typing import List

from dash.exceptions import PreventUpdate
from dash import callback, dcc, html, Input, Output, State

from dashboard.app import app

from dashboard.apiaccess import get_all_rooms, get_all_measures, get_merged_data

@app.callback(
    Output("collapse", "is_open"),
    [Input("toggle", "n_clicks")],
    [State("collapse", "is_open")],
)
def toggle_collapse(n, is_open):
    print('toggle_collapse')
    if n:
        return not is_open
    return is_open

@callback(
    Output('card_text_rooms', 'children'),
    Output('card_text_measurements','children'),
    Output('dropdown_rooms', 'options'),
    Output('dropdown_measures', 'options'),
    Input('available_rooms', 'data'),
    Input('available_measures', 'data'),
    Input('date_picker_range_dates', 'end_date')
)
def fill_dropdown_rooms(all_rooms: List[str], all_measures: List[str], _):
    print('fill_dropdown_rooms')
    if all_rooms is None:
        raise PreventUpdate
    print(f'fill_dropdown_rooms {all_rooms}')
    return f'ROOMS: {len(all_rooms)}', f'MEASURES: {len(all_measures)}', all_rooms, all_measures

@callback(
    Output('available_rooms', 'data'),
    Output('available_measures', 'data'),
    Input('submit_button', 'n_clicks')
)
def initialize(n_clicks: int):
    print(f'initialize {n_clicks}')
    if n_clicks:
        # prevent the None callbacks is important with the store component.
        # you don't want to update the store for nothing.
        raise PreventUpdate
    print('initialize rooms')
    rooms = get_all_rooms()
    print('initialize measures')
    measures = get_all_measures()
    print(f'initialize: {rooms=} {measures=}')
    return rooms, measures

@callback(
    Output('current_timeline', 'data'),
    State("date_picker_range_dates", "start_date"),
    State("date_picker_range_dates", "end_date"),
    State("dropdown_measures", "value"),
    State("dropdown_rooms", "value"),
    State("radio_items_time_group", "value"),
    Input('submit_button', 'n_clicks')
)
def get_merged_timeline(start: str, end: str, measures: List[str], rooms: List[str], timegroup: str, n_clicks: int):
    print(f'get_merged_timeline {n_clicks=}')
    if not n_clicks:
        raise PreventUpdate
    print(f'get_merged_timeline {start=} {end=} {measures=} {rooms=}')
    if not (start and  end and measures and rooms):
        raise PreventUpdate
    print(f'get_merged_timeline >>>>>>>>>>>')
    room_to_query = None if len(rooms) > 1 else rooms[0]
    measure_to_query = None if len(measures) > 1 else measures[0]
    json_data = get_merged_data(start_date=start,
                                end_date=end,
                                measure=measure_to_query,
                                room=room_to_query,
                                tg=timegroup)
    print(f'<<<<<<<<<<<<<<get_merged_timeline: {json_data=}')
    return json_data
    
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
