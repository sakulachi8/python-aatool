import logging
import pandas as pd
from functools import lru_cache

import os
# Get the absolute path of the directory that the current script is in
current_dir = os.path.dirname(os.path.abspath(__file__))
# Change the current working directory to script_dir
os.chdir(current_dir)

from dash import Dash, dcc, html, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO

from data_processor.data_processor import run
from models.app_functions import display_simulated_ef_with_random, create_table, create_dropdown
from models.app_functions import get_allocations_bar_chart, get_heatmap, get_asset_allocation, get_returns_chart, get_table

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

risk_free_rate = 0.02

logger.info('Reading data')
data = pd.read_csv(current_dir + r"/data_processor/tests/test_data/table.csv")
name = data['name'].unique()
data.drop(columns=['name'], inplace=True)

@lru_cache(maxsize=None)
def get_results():
    results_data, weights_data, analytics, metadata_dict, message = run(data, start='2023-01-01', end='2023-07-01', freq='M', delete_pickle=True, risk_free_rate = 0.02, num_portfolio_cycles = 1000, comments="")
    return results_data, analytics, metadata_dict, message

df = data.copy()
categories = df['category'].unique()

dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
dash_app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR, dbc_css])
app = dash_app.server

header = html.H4(
    "Investment Data", className="bg-primary text-white p-2 mb-2 text-center"
)


table = create_table(df)
dropdown = create_dropdown(categories)
controls = dbc.Card([dropdown], body=True,)

progress_bar = html.Div(
    (dcc.Interval(id='progress-interval', interval=500, n_intervals=0),
    dbc.Progress(id='progress-bar', animated=True, striped=True)),
    style={'margin': '10px'}
)

button = html.Button('Calculate Efficient Frontier', id='calculate-button', n_clicks=0)

def create_ef():
    return dcc.Graph(id="ef-graph")

def create_heatmap():
    return dcc.Graph(id="heatmap-graph")

tab1 = dcc.Tab([create_heatmap()], label="Line Chart", value="line_chart")
tab2 = dcc.Tab([create_ef()], label="Efficient Frontier", value="efficient_frontier")
tab3 = dcc.Tab([get_table(get_results())], label="Table", className="p-4", value="table")
# tab5 = dcc.Tab([dcc.Graph(id="scatter-chart")], label="Covariance Heatmap", value="covariance_heatmap")
# tab6 = dcc.Tab([get_asset_allocation(get_results())], label="Asset Allocation Pie", value="asset_allocation")
tab7 = dcc.Tab([get_allocations_bar_chart(data)], label="Asset Allocations Bar", value="asset_allocations")
tab8 = dbc.Tab([table], label="Table", className="p-4")

tabs = dcc.Tabs(
    [tab1,tab2,tab3,tab7,tab8]
    # [tab2, tab8]
)

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
                dbc.Col([tabs, html.Div(id="tab-content")], width=8),
            ]
        ),
        dbc.Row(button),
        dbc.Row(progress_bar),
    ],
    
    fluid=True,
    className="dbc",
)





@dash_app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("category", "value"),
)
def render_tab_content(active_tab, category):  # Update the argument name
    dff = df[df['category'] == category]
    data = dff.to_dict("records")
    result_dict, metadata_dict = get_results()

    if active_tab == "table":
        return create_table(dff)
    elif active_tab == "efficient_frontier":
        fig = display_simulated_ef_with_random(result_dict)
        return dcc.Graph(figure=fig)
    elif active_tab == "line_chart":
        return get_returns_chart(result_dict)
    elif active_tab == "covariance_heatmap":
        fig = get_heatmap(result_dict)
        return dcc.Graph(figure=fig)
    elif active_tab == "asset_allocation":
        return get_asset_allocation(result_dict)
    elif active_tab == "asset_allocations":
        return get_allocations_bar_chart(data)
    else:
        return "No content available."


@dash_app.callback(Output('table-container', 'children'),
              Input('calculate-button', 'n_clicks'),
              Input('page-load', 'page_load'))
def display_datatable(n_clicks):
    return create_table(df)

if __name__ == "__main__":
    from waitress import serve
    serve(dash_app.server)

