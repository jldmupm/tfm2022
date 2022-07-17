from datetime import date, datetime

from dashboard.styles import CARD_TEXT_STYLE, CONTENT_STYLE, TEXT_STYLE, SIDEBAR_STYLE
from dash import dcc, html
import dash_bootstrap_components as dbc

# we use the Row and Col components to construct the sidebar header
# it consists of a title, and a toggle, the latter is hidden on large screens
sidebar_header = dbc.Row(
    [
        dbc.Col(
            html.Button(
                # use the Bootstrap navbar-toggler classes to style the toggle
                html.Span("Get", className="navbar-toggler-icon"),
                className="navbar-toggler",
                # the navbar-toggler classes don't set color, so we do it here
                style={
                    "color": "rgba(0,0,0,.5)",
                    "border-color": "rgba(0,0,0,.1)",
                },
                id="toggle",
            ),
            # the column containing the toggle will be only as wide as the
            # toggle, resulting in the toggle being right aligned
            width="auto",
            # vertically align the toggle in the center
            align="center",
        ),
    ]
)

controls = html.Div([
        html.P('Rooms', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='dropdown_rooms',
            value=['value1'],  # default value
            multi=True
        ),
        html.Br(),
        html.P('Date Range Selector', style={
            'textAlign': 'center'
        }),
        dcc.DatePickerRange(
            id='date_picker_range_dates',
            min_date_allowed=date(2021, 1, 1),
            max_date_allowed=date(2030, 12, 31),
            initial_visible_month=datetime.utcnow().date(),
            start_date=datetime.utcnow().date(),
            end_date=datetime.utcnow().date()),
        html.Br(),
        html.P('Measure selector', style={
            'textAlign': 'center'
        }),
        dcc.Dropdown(
            id='dropdown_measures',
            value=['value1'],
            multi=True
        ),
        html.Br(),
        html.P('Time grouping', style={
            'textAlign': 'center'
        }),
        dbc.Card([dbc.RadioItems(
            id='radio_items_time_group',
            options=[{
                'label': 'Horario',
                'value': '1H'
            },
            {
                'label': 'Diario',
                'value': '1D'
            },
            {
                'label': 'Mensual',
                'value': '1M'
            }
            ],
            value='1M',
            style={
                'margin': 'auto'
            }
        )]),
        html.Br(),
        dbc.Button(
            id='submit_button',
            n_clicks=0,
            children='Query',
            color='primary'
        ),
])


sidebar = html.Div(
    [
        sidebar_header,
        dbc.Collapse([
            html.H2('Parameters', style=TEXT_STYLE),
            html.Hr(),
            controls,
        ],
        id="collapse"),
    ],
    style=SIDEBAR_STYLE,
)
