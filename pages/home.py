import dash
from dash import dcc, html, callback, Output, Input, State
import plotly.express as px
import dash_bootstrap_components as dbc

dash.register_page(__name__, path='/', name='Home') 


# Define your input group
input_group = dbc.InputGroup(
    [
        dbc.Input(id='home-unique-key', placeholder="Enter unique ID", className="form-control"),
        # dbc.NavItem(dbc.NavLink("Get Reports", href="/reports", id='get-reports-button', className="active ml-2")),
        dbc.Button("Get Reports", id='get-reports-button', color="primary", className="active ml-2", href='/reports', n_clicks=0),
    ],
    className="mb-3",
)

# Define your new portfolio button
new_portfolio_button = dbc.Button('Load Data', id='load-data-button', color="primary", size="md", className="w-100", href='/load-data')


# def layout(input_group,new_portfolio_button):
# # Define your layout
layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        input_group,
                        html.Div('OR', style={'text-align': 'center'}),
                        new_portfolio_button
                    ],
                    sm={"size": 12}, md = {'size' : 5, 'offset' : 3}
                )
            ],
            align="center",
        )
    ]
)


@callback(
        Output('url', 'pathname'),
        Input('get-reports-button', 'n_clicks'),
)

def update_path_name(n):
    if n > 0:
        return "/reports"
    else:
        return None


@callback(
    Output('data-store', 'data'),
    Input('home-unique-key', 'value'),
    State('load-data-storage', 'data')
)
def update_graph(value,load_data_storage):
    if value:
        data_storage_count = 1
        if load_data_storage:
            data_storage_count = load_data_storage.get('count') + 1   
        return {"hash_key": value,
                "count": data_storage_count}
    return None


# @callback(
#     Output('home-unique-key', 'value'),
#     Input('new-portfolio-button', 'n_clicks')
# )
# def update_graph(n_clicks):
#     if n_clicks:
#         return 'New Submit Button Clicked'
#     return None
