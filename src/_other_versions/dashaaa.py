import dash as dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import pandas as pd
import processData
import pymongo

app = dash.Dash(__name__)

# Define the layout of the dashboard
app.layout = html.Div([
    html.H1("Financial Dashboard"),
    dcc.Upload(
        id="upload-data",
        children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
        style={
            "width": "100%",
            "height": "60px",
            "lineHeight": "60px",
            "borderWidth": "1px",
            "borderStyle": "dashed",
            "borderRadius": "5px",
            "textAlign": "center",
        },
        multiple=True,
    ),
    dcc.Dropdown(
        id="benchmark-dropdown",
        options=[
            {"label": "S&P 500", "value": "SP500"},
            {"label": "NASDAQ", "value": "NASDAQ"},
            {"label": "Dow Jones", "value": "DowJones"},
        ],
        value="SP500",
    ),
    dcc.Input(
        id="simulation-params",
        type="number",
        placeholder="Number of Simulations",
        value=1000,
    ),
    html.Button("Process Data", id="process-button"),
    dcc.Graph(id="efficient-frontier-graph"),
    dcc.Graph(id="benchmark-distribution-graph"),
    dcc.Graph(id="portfolio-performance-graph"),
])

# Define the callback for uploading data
@app.callback(
    Output("upload-data", "children"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
)
def update_output(contents, filename):
    if contents is not None:
        # Read in the CSV file
        df = pd.read_csv(contents[0], parse_dates=True)
        return html.Div([
            html.H5(filename),
            html.Hr(),
            html.P(f"{len(df)} rows of data."),
        ])

# Define the callback for processing data
@app.callback(
    [
        Output("efficient-frontier-graph", "figure"),
        Output("benchmark-distribution-graph", "figure"),
        Output("portfolio-performance-graph", "figure"),
    ],
    Input("process-button", "n_clicks"),
    State("upload-data", "contents"),
    State("benchmark-dropdown", "value"),
    State("simulation-params", "value"),
)
def process_data(n_clicks, contents, benchmark, num_simulations):
    if n_clicks is not None:
        # Read in the CSV file
        df = pd.read_csv(contents[0], parse_dates=True)

        # Process the data using the processData module
        processed_data = processData.process(df)

        # Perform Monte Carlo simulation
        simulation_data = processData.simulate(processed_data, num_simulations)

        # Generate visualizations of the processed data
        efficient_frontier_graph = processData.plot_efficient_frontier(simulation_data)
        benchmark_distribution_graph = processData.plot_benchmark_distribution(simulation_data, benchmark)
        portfolio_performance_graph = processData.plot_portfolio_performance        # Return the figures
        return efficient_frontier_graph, benchmark_distribution_graph, portfolio_performance_graph

if __name__ == "main":
    app.run_server(debug=True)

