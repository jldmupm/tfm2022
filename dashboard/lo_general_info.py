from dashboard.styles import CARD_TEXT_STYLE, CONTENT_STYLE, TEXT_STYLE
from dash import dcc, html
import dash_bootstrap_components as dbc

general_info_row = dbc.Row([
    dbc.Col(
        dbc.Card(
            [

                dbc.CardBody(
                    [
                        html.H4(id='card_title_rooms', children=['Rooms'], className='card-title',
                                style=CARD_TEXT_STYLE),
                        html.P(id='card_text_rooms', children=['To show the Number of Rooms.'], style=CARD_TEXT_STYLE),
                    ]
                )
            ]
        ),
        md=4
    ),
    dbc.Col(
        dbc.Card(
            [

                dbc.CardBody(
                    [
                        html.H4(id='card_title_measurements', children='Measurement', className='card-title', style=CARD_TEXT_STYLE),
                        html.P(id='card_text_measurements',children='To show the number of different measurements.', style=CARD_TEXT_STYLE),
                    ]
                ),
            ]

        ),
        md=4
    ),
    dbc.Col(
        dbc.Card(
            [
                dbc.CardBody(
                    [
                        html.H4(id='card_title_dates', children='Dates', className='card-title', style=CARD_TEXT_STYLE),
                        html.P(id='card_text_dates',children='To show the date ranges', style=CARD_TEXT_STYLE),
                    ]
                ),
            ]

        ),
        md=4
    )],
    align='center')

