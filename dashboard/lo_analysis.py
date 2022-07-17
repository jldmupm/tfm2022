from dashboard.styles import CARD_TEXT_STYLE, CONTENT_STYLE, TEXT_STYLE, SIDEBAR_STYLE
from dash import dcc, html
import dash_bootstrap_components as dbc


analysis_header = dbc.Row(
    [
        dbc.Col(
            html.Button(
                # use the Bootstrap navbar-toggler classes to style the toggle
                html.Span("Analize"),
                className="navbar-toggler",
                # the navbar-toggler classes don't set color, so we do it here
                style={
                    "color": "rgba(0,0,0,.5)",
                    "border-color": "rgba(0,0,0,.1)",
                },
                id="toggle_analysis",
            ),
            # the column containing the toggle will be only as wide as the
            # toggle, resulting in the toggle being right aligned
            width="auto",
            # vertically align the toggle in the center
            align="center",
        )
    ]
)

analysis_collapse = dbc.Row(
    dbc.Col(
        dbc.Collapse(
            dbc.Card([
                dbc.CardHeader("Analysis Result"),
                dbc.CardBody(children=[
                    dcc.Graph(id="graph_lr_predict"),
                    dcc.Graph(id="graph_correlations")
                ])]),
            id="collapse_analysis",
            is_open=False,
        ),
    )
)
