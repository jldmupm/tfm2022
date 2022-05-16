# -*- coding: utf-8 -*-
import datetime

from dash import Dash, dcc, html, Input, Output

import src.analisis.df_load as df_load

df = df_load.load_dataframe()

minDay = datetime.datetime.utcnow()
maxDay = datetime.datetime.utcnow() + datetime.timedelta(days=10)

app = Dash(name="UI Data Explorer")


header = html.H1(children="UI Data Explorer")
main_graph = html.Div(id="main_graph")
main_table = html.Div()
year = dcc.RangeSlider(minDay, maxDay, 1, tooltip={"placement": "bottom", "always_visible": True})

app.layout = html.Div(children=[
    header,
    main_graph,
    main_table,
    year,
])

@app.callback(Output("main_graph", ""))

if __name__ == '__main__':
    app.run_server(debug=True)
