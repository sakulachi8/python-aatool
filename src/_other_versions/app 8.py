"""
****** Important! *******
If you run this dash_app locally, un-comment line 113 to add the ThemeChangerAIO component to the layout
"""
import pandas as pd
from dash import Dash, dcc, html, dash_table, Input, Output, callback
import plotly.express as px
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import ThemeChangerAIO, template_from_url
from dash.dependencies import Input, Output, State


from data_processor.data_processor import run
from models.app_functions import display_simulated_ef_with_random, create_table, create_dropdown
from models.app_functions import get_allocations_bar_chart, get_heatmap, get_asset_allocation, get_returns_chart, get_table


print('Running Test Data')
df = pd.read_csv('data_processor/tests/test_data/table.csv')
df = df.drop(columns=['name'])
result, metadata_dict = run(df)

categories = df.category.unique()
tickers = list(metadata_dict.keys())
dates = result['date_range']

full, name, asset_type, exchange, currency = [], [], [], [], []
for ticker in tickers:
    i = 0
    if len(metadata_dict[ticker]['DocumentTitle'].split(', ')) == 4: i=1
    full.append(metadata_dict[ticker]['DocumentTitle'])
    name.append(metadata_dict[ticker]['DocumentTitle'].split(', ')[0])
    asset_type.append(metadata_dict[ticker]['DocumentTitle'].split(', ')[1])
    exchange.append(metadata_dict[ticker]['DocumentTitle'].split(', ')[2+i])
asset_type = list(set(asset_type))
exchange = list(set(exchange))

# stylesheet with the .dbc class
dbc_css = "https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates/dbc.min.css"
dash_app = Dash(__name__, external_stylesheets=[dbc.themes.ZEPHYR, dbc_css])
app = dash_app.server

header = html.H4(
    "Test WebApp for Sayers Asset Allocation", className="bg-primary text-white p-2 mb-2 text-center"
)

table = html.Div(
    dash_table.DataTable(
        id="table-data",
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
        dbc.Label("Select Exchange"),
        dcc.Dropdown(
            id="indicator",
            options=[{"label": i, "value": i} for i in [ex for ex in exchange if ex != '']+['All']],
            value="pop",
            clearable=False,
        ),
    ],
    className="mb-4",
)

checklist = html.Div(
    [
        dbc.Label("Select Asset Type"),
        dbc.Checklist(
            id="categories",
            options=[{"label": i, "value": i} for i in categories],
            value=categories,
            inline=True,
        ),
    ],
    className="mb-4",
)

slider = html.Div(
    [
        dbc.Label("Select Dates"),
        dcc.RangeSlider(
            id="dates",
            min=dates[0],
            max=dates[-1],
            step=5,
            marks={str(year): str(year) for year in dates},
            tooltip={"placement": "bottom", "always_visible": True},
            value=[dates[2], dates[-2]],
            className="p-0",
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
    [dropdown, checklist, slider],
    body=True,
)

tab1 = dbc.Tab([dcc.Graph(id="line-chart")], label="Line Chart")
tab2 = dbc.Tab([dcc.Graph(id="scatter-chart")], label="Scatter Chart")
tab3 = dbc.Tab([table], label="Table", className="p-4")
tabs = dbc.Card(dbc.Tabs([tab1, tab2, tab3]))

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
                dbc.Col([tabs, colors], width=8),
            ]
        ),
    ],
    fluid=True,
    className="dbc",
)


@callback(
    Output("line-chart", "figure"),
    Output("scatter-chart", "figure"),
    Output("table-data", "data"),
    Input("asset_type", "value"),
    Input("exchange", "value"),
    Input("dates", "value"),
    Input(ThemeChangerAIO.ids.radio("theme"), "value"),
)
def update_line_chart(asset_type, exchange, dates, theme):
    if exchange == [] or asset_type is None:
        return {}, {}, []

    # dff = df2[df2.year.between(yrs[0], yrs[1])]
    # dff = dff[dff.continent.isin(continent)]
    data = df.to_dict("records")

    df = pd.read_csv('data_processor/tests/test_data/table.csv')
    df = df.drop(columns=['name'])

    result_dict, _ = run(data, risk_free_rate=0.02)
    fig_scatter = display_simulated_ef_with_random(result_dict)
    fig_scatter = fig_scatter.update_layout(template=template_from_url(theme))
    fig_scatter = dcc.Graph(figure=fig_scatter)

    fig = px.bar_polar(
        df,
        r="pop",
        theta="category",
        color="holding",
        template=template_from_url(theme),
        title="Gapminder %s: %s theme" % (dates[1], template_from_url(theme)),
        height=700,
        color_discrete_sequence=px.colors.sequential.Plasma_r,
        # color_discrete_sequence=px.colors.sequential.Plasma_r,
    )

    

    
    # px.scatter(
    #     df.query(f"year=={yrs[1]} & continent=={continent}"),
    #     x="gdpPercap",
    #     y="lifeExp",
    #     size="pop",
    #     color="continent",
    #     log_x=True,
    #     size_max=60,
    #     template=template_from_url(theme),
    #     title="Gapminder %s: %s theme" % (yrs[1], template_from_url(theme)),
    # )

    return fig, fig_scatter, df


if __name__ == "__main__":
    from waitress import serve
    serve(dash_app.server, host="127.0.0.1", port=8050)