from flask import Flask
from dash import Dash

import dash_bootstrap_components as dbc

server = Flask('Analysis Dashboard')
app = Dash(url_base_pathname='/',
           server=server,
           external_stylesheets=[dbc.themes.BOOTSTRAP,
                                 dbc.icons.BOOTSTRAP])
#app.config.suppress_callback_exceptions = True
