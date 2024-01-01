import logging
import pandas as pd
from functools import lru_cache

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
data = pd.read_csv('data_processor/tests/test_data/table.csv')
name = data['name'].unique()
data.drop(columns=['name'], inplace=True)

result_dict, metadata_dict = run(data, risk_free_rate)

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

# progress_bar = html.Div(
#     (dcc.Interval(id='progress-interval', interval=500, n_intervals=0),
#     dbc.Progress(id='progress-bar', animated=True, striped=True)),
#     style={'margin': '10px'}
# )

button = html.Button('Calculate Efficient Frontier', id='calculate-button', n_clicks=0)

def create_ef():
    return dcc.Graph(id="ef-graph")

tab1 = dbc.Tab([get_returns_chart(result_dict)], label="Line Chart")
tab2 = dbc.Tab([create_ef()], label="Efficient Frontier") #, progress_bar
tab3 = dbc.Tab([get_table(result_dict)], label="Table", className="p-4")
tab5 = dbc.Tab([get_heatmap(result_dict)], label="Covariance Heatmap")
tab6 = dbc.Tab([get_asset_allocation(result_dict)], label="Asset Allocation")
tab7 = dbc.Tab([get_allocations_bar_chart(data)], label="Asset Allocations")
tabs = dbc.Card(dbc.Tabs([
    dbc.Tab(id="line_chart", label="Line Chart"),
    dbc.Tab([create_ef()], label="Efficient Frontier", tab_id="efficient_frontier"),
    dbc.Tab(id="table", label="Table", className="p-4"),
    dbc.Tab(id="covariance_heatmap", label="Covariance Heatmap"),
    dbc.Tab(id="asset_allocation", label="Asset Allocation"),
    dbc.Tab([get_allocations_bar_chart(data)], label="Asset Allocations", tab_id="asset_allocations"),
], id="tabs"))




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
        
    ],
    
    fluid=True,
    className="dbc",
)


@dash_app.callback(
    Output('ef-graph', 'figure'),
    # Output('progress-bar', 'value'),
    Input('calculate-button', 'n_clicks')
)
def update_ef_graph(n_clicks):
    if n_clicks > 0:
        
        fig = display_simulated_ef_with_random(result_dict)
        #progress = 100
        return fig#, progress
    else:
        return {}, 0
    
import json, numpy as np
import pandas as pd

def numpy_arrays_to_lists(obj):
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, pd.Series):
        return obj.to_dict()
    elif isinstance(obj, dict):
        return {k: numpy_arrays_to_lists(v) for k, v in obj.items()}
    else:
        return obj

# Convert the result_dict
result_dict_lists = numpy_arrays_to_lists(result_dict)

# Add this hidden Div to your layout
hidden_div = html.Div(id='result_dict', children=json.dumps(result_dict_lists), style={'display': 'none'})

@dash_app.callback(
    Output("tab-content", "children"),
    Input("tabs", "active_tab"),
    Input("category", "value"),
    Input('calculate-button', 'n_clicks'),
    State('result_dict', 'children'),  # Update this line
)
def render_tab_content(active_tab, category, n_clicks, result_dict_json):  # Update the argument name
    result_dict = json.loads(result_dict_json) 
    dff = df[df['category'] == category]
    data = dff.to_dict("records")

    if active_tab == "table":
        return get_table(result_dict)
    elif active_tab == "efficient_frontier":
        if n_clicks > 0:
            fig = display_simulated_ef_with_random(result_dict)
            return dcc.Graph(figure=fig)
        else:
            return dcc.Graph(figure={})
    elif active_tab == "line_chart":
        return get_returns_chart(result_dict)
    elif active_tab == "covariance_heatmap":
        return get_heatmap(result_dict)
    elif active_tab == "asset_allocation":
        return get_asset_allocation(result_dict)
    elif active_tab == "asset_allocations":
        return get_allocations_bar_chart(data)
    else:
        return "No content available."


@dash_app.callback(Output('table-container', 'children'),
              Input('calculate-button', 'n_clicks'))
def display_datatable(n_clicks):
    return create_table(df)

if __name__ == "__main__":
    from waitress import serve
    serve(dash_app.server, host="127.0.0.1", port=8050)

