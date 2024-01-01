import logging
import pandas as pd
import numpy as np
from functools import lru_cache
from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
from dash.dash_table.Format import Group
import plotly.express as px
import plotly.graph_objs as go
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO
from dash.dependencies import Input, Output, State

from data_processor.data_processor import run
from models.app_functions import display_simulated_ef_with_random, create_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

risk_free_rate = 0.02

logger.info('Reading data')
data = pd.read_csv('data_processor/tests/test_data/table.csv')
name = data['name'].unique()
data.drop(columns=['name'], inplace=True)

result_dict, metadata_dict = run(data, risk_free_rate)

df = data.copy()
categories = df['category'].unique()

# stylesheet with the .dbc class
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
dash_app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR, dbc_css])
app = dash_app.server

header = html.H4(
    "Investment Data", className="bg-primary text-white p-2 mb-2 text-center"
)

table = create_table(df)


def create_dropdown(categories):
    return html.Div(
        [
            dbc.Label("Select category"),
            dcc.Dropdown(
                id="category",
                options=[{"label": i, "value": i} for i in categories],
                value=categories[0],
                clearable=False,
            ),
        ],
        className="mb-4",
    )

dropdown = create_dropdown(categories)

controls = dbc.Card([dropdown], body=True,)

def create_tabs():
    return html.Div(
        [
            dbc.Tabs(
                [
                    dbc.Tab(label="Table", tab_id="table"),
                    dbc.Tab(
                        label="Efficient Frontier", tab_id="efficient_frontier"
                    ),
                ],
                id="tabs",
                active_tab="table",
            ),
            html.Div(id="tab-content"),
        ]
    )

tabs = create_tabs()

dash_app.layout = dbc.Container(
    [
        header,
        dbc.Row(
            [
                dbc.Col(
                    [
                        controls,
                        ThemeChangerAIO(aio_id="theme")
                    ],
                    width=4,
                ),
                #dbc.Col([tabs, colors], width=8),
            ]
        ),
    ],
    fluid=True,
    className="dbc",
)

@callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("category", "value"),
)

def render_tab_content(active_tab, category):
    dff = df[df['category'] == category]
    data = dff.to_dict("records")
    if active_tab == "table":
        return create_table(dff)
    elif active_tab == "efficient_frontier":
        fig = display_simulated_ef_with_random(result_dict)
        return dcc.Graph(figure=fig)
    else:
        return "No content available."
    
# if __name__ == "__main__":
#     dash_app.run_server(debug=True)
if __name__ == "__main__":
    from waitress import serve
    serve(dash_app.server, host="127.0.0.1", port=8050)
