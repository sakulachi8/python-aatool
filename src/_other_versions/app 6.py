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
from models.app_functions import display_simulated_ef_with_random, create_table, create_dropdown

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

risk_free_rate = 0.02

logger.info('Reading data')
data = pd.read_csv('data_processor/tests/test_data/table.csv')
name = data['name'].unique()
data.drop(columns=['name'], inplace=True)

# Use the @lru_cache decorator to cache the results of the run() function
@lru_cache(maxsize=None)
def get_results():
    return run(data, risk_free_rate)

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

dropdown = create_dropdown(categories)

controls = dbc.Card([dropdown], body=True,)

# graph_ef = create_ef()

progress_bar = html.Div(
    (dcc.Interval(id='progress-interval', interval=500, n_intervals=0),
    dbc.Progress(id='progress-bar', animated=True, striped=True)),
    style={'margin': '10px'}
)

# Add a button to trigger the efficient frontier calculation
button = html.Button('Calculate Efficient Frontier', id='calculate-button', n_clicks=0)

theme_colors = [
    "primary",
    "secondary",
    "success",
    "warning",
    "danger",
    "info",
    "light",
    "dark",
    "link",
]


def create_ef():
    return dcc.Graph(id="ef-graph")

tab1 = dbc.Tab([dcc.Graph(id="line-chart")], label="Line Chart")
tab2 = dbc.Tab([create_ef()], label="Efficient Frontier")
tab3 = dbc.Tab([table], label="Table", className="p-4")
tabs = dbc.Card(dbc.Tabs([tab1, tab2, tab3]))

dash_app.layout = dbc.Container(
    [
        header,
        dbc.Row(
            [
                dbc.Col(
                    [
                        controls
                    ],
                    width=4,
                ),
                dbc.Col([tabs], width=8),
            ]
        ),
        dbc.Row(button),
        dbc.Row(progress_bar),
    ],
    
    fluid=True,
    className="dbc",
)

# Get the results using the get_results() function
result_dict, metadata_dict = get_results()

@dash_app.callback(
    Output('ef-graph', 'figure'),
    Input('calculate-button', 'n_clicks')
)
def update_ef_graph(n_clicks):
    if n_clicks > 0:
        result_dict, metadata_dict = get_results()
        fig = display_simulated_ef_with_random(result_dict)
        return fig
    else:
        return {}


# Update the progress bar value based on the progress of the tasks
@dash_app.callback(
    Output('progress-bar', 'value'),
    Input('progress-interval', 'n_intervals')
)
def update_progress(n):
    # Calculate the progress based on the length of the results dictionary
    progress = int((len(result_dict) / len(metadata_dict)) * 100)
    return progress

@callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("category", "value"),
    Input('calculate-button', 'n_clicks'),
)
def render_tab_content(active_tab, category, n_clicks):
    dff = df[df['category'] == category]
    data = dff.to_dict("records")
    if active_tab == "table":
        return create_table(dff)
    elif active_tab == "efficient_frontier":
        if n_clicks > 0:
            # Call the get_results() function to calculate the efficient frontier
            result_dict, metadata_dict = get_results()
            fig = display_simulated_ef_with_random(result_dict)
            return dcc.Graph(figure=fig)
        else:
            # Return an empty graph if the button is not clicked yet
            return dcc.Graph(figure={})
    else:
        return "No content available."

# Add a callback function to display the datatable when the app is loaded
@dash_app.callback(Output('table-container', 'children'),
              Input('calculate-button', 'n_clicks'))
def display_datatable(n_clicks):
    return create_table(df)

if __name__ == "__main__":
    from waitress import serve
    serve(dash_app.server, host="127.0.0.1", port=8050)