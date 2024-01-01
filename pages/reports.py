import dash
from dash import dcc, html, callback, Output, Input, State, ctx
import dash_bootstrap_components as dbc
from models.app_functions import get_dash_table_by_hashkey

dash.register_page(__name__, name='Reports')

layout = html.Div([
    dcc.Loading(
        id="loading-component",
        type="circle",
        style= { 'marginTop' : '50%'},
        children=[html.Div(id='portfolio-detail-graphs')]
    )
])

@callback(
    [Output('portfolio-detail-graphs', 'children')],
    [Input('data-store', 'data'), Input('load-data-storage', 'data')]
)
def update_output(data_store, load_data_storage):
    if data_store or load_data_storage:
        if data_store:
            data_store_count = data_store.get('count')
        else:
            data_store_count = 0

        if load_data_storage:
            load_data_storage_count = load_data_storage.get('count')
        else:
            load_data_storage_count = 0

        if data_store_count >= load_data_storage_count:
            unique_key = data_store.get('hash_key')
        else:
            unique_key = load_data_storage.get('hash_key')

        graphs = get_dash_table_by_hashkey(unique_key)
        return [graphs]
    return None