from dash import Dash, dcc, html, dash_table, Input, Output, callback
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url

df = px.data.gapminder()
years = df.year.unique()
continents = df.continent.unique()
response_vars = ['gdpPercap', 'lifeExp', 'pop']

# stylesheet with the .dbc class
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
dash_app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR, dbc_css])
app = dash_app.server

header = html.H4(
    "Test WebApp for Sayers Asset Allocation", className="bg-primary text-white p-2 mb-2 text-center"
)

table = html.Div(
    dash_table.DataTable(
        id="table",
        columns=[{"name": i, "id": i, "deletable": True} for i in df.columns],
        data=df.to_dict("records"),
        page_size=10,
        editable=True,
        cell_selectable=True,
        filter_action="native",
        sort_action="native",
        style_table={"overflowX": "auto"},
        row_selectable="multi",
    ),
    className="dbc-row-selectable",
)

dropdown = html.Div(
    [
        dbc.Label("Select indicator (y-axis)"),
        dcc.Dropdown(
            options=[{"label": i, "value": i} for i in response_vars],
            value=response_vars[0],
            id="response-var",
            clearable=False,
        ),
    ],
    className="mb-4",
)

checklist = html.Div(
    [
        dbc.Label("Select Continents"),
        dbc.Checklist(
            id="continents",
            options=[{"label": i, "value": i} for i in continents],
            value=continents,
            inline=True,
        ),
    ],
    className="mb-4",
)

slider = html.Div(
    [
        dbc.Label("Select Years"),
        dcc.RangeSlider(
            years[0],
            years[-1],
            5,
            id="years",
            marks=None,
            tooltip={"placement": "bottom", "always_visible": True},
            value=[years[2], years[-2]],
            className="p-0",
        ),
    ],
    className="mb-4",
)

graph_selector = html.Div(
    [
        dbc.Label("Select Graph"),
        dcc.Dropdown(
            options=[{"label": "Line Chart", "value": "line-chart"},
                     {"label": "Scatter Chart", "value": "scatter-chart"},
                     {"label": "Table", "value": "table"}],
            value="line-chart",
            id="graph-selector",
            clearable=False,
        ),
    ],
    className="mb-4",
)

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
colors = html.Div(
    [dbc.Button(f"{color}", color=f"{color}", size="sm") for color in theme_colors]
)
colors = html.Div(["Theme Colors:", colors], className="mt-2")


controls = dbc.Card(
    [dropdown, checklist, slider, graph_selector],
    body=True,
)

tabs = dbc.Card(dbc.Tabs([
    dbc.Tab([dcc.Graph(id="scatter-chart")], label="Scatter Chart"),
    dbc.Tab([table], label="Table", className="p-4")
]))

dash_app.layout = dbc.Container([
    header,
    dbc.Row([
        dbc.Col([
            controls,
            ThemeChangerAIO(aio_id="theme")
        ], width=4),
        dbc.Col([
            tabs,
            colors
        ], width=8)
    ])
], fluid=True, className="dbc")

@app.callback(
    [
        Output("line-chart", "figure"),
        Output("scatter-chart", "figure"),
        Output("table", "data")
    ],
    [
        Input("indicator", "value"),
        Input("continents", "value"),
        Input("years", "value"),
        Input(ThemeChangerAIO.ids.radio("theme"), "value")
    ]
)
def update_graphs(indicator, continents, years, theme):
    if continents == [] or indicator is None:
        return {}, {}, []

    df_filtered = df[df.year.between(years[0], years[1])]
    df_filtered = df_filtered[df_filtered.continent.isin(continents)]
    table_data = df_filtered.to_dict("records")

    line_chart_fig = px.line(
        df_filtered,
        x="year",
        y=indicator,
        color="continent",
        line_group="country",
        template=template_from_url(theme),
    )

    scatter_chart_fig = px.scatter(
        df_filtered,
        x="gdpPercap",
        y="lifeExp",
        size="pop",
        color="continent",
        log_x=True,
        size_max=60,
        template=template_from_url(theme),
        title="Gapminder",
    )

    return line_chart_fig, scatter_chart_fig, table_data

if __name__ == "__main__":
    dash_app.run_server(debug=True)

