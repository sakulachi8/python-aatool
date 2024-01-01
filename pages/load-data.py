from dash import dcc, html, dash_table, callback
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import pandas as pd
import dash
import datetime
import base64
import io
import logging

from models.app_functions import simulate_new_profile, generate_hash_key, check_if_hash_key_exists

dash.register_page(__name__, name='Load Data')


layout = dbc.Container([
    dbc.Row([
        dbc.Col(dcc.Upload(dbc.Button('Load from CSV'), id='upload-data', className='mt-2', style={'float': 'left', 'color':'secondary'}, multiple=True), md={'size': 3}),
    ]),
    dbc.Row([
        dbc.Col(className="control-overflow",children=[
            dash_table.DataTable(
                id='portfolio-data-table',
                editable=True,
                page_size=17,
            ),
        ], sm={'size' : 5}, md={'size' : 5} ),
        dbc.Col([
            dbc.Row([
                dbc.Col(dbc.Label('Portfolio Name:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.Input(id='portfolio-name', type='text', value='Test Portfolio - TESTING AFTER BREAK', className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Client ID:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.Input(id='client-id', type='text', value='1099', className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Delete Pickle:', className='mb-1 text-end'), width=3),
                dbc.Col(dbc.InputGroup([
                    dbc.RadioItems(
                        id='delete-pickle',
                        options=[{'label': 'True', 'value': '1'}, {'label': 'False', 'value': '0'}],
                        value='1',
                        inline=True,
                        className='mb-3',
                        style={'margin-right': '10px'},
                        inputClassName='mr-2',
                    )
                ]), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Simulations:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.Input(id='simulations', type='number', value=10000, className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('On Conflict:', className='mb-1 text-end'), width=3),
                dbc.Col(dbc.InputGroup([
                    dcc.RadioItems(
                        id='on-conflict',
                        options=[{'label': 'Update', 'value': 'Update'}, {'label': 'Do Nothing', 'value': 'DoNothing'}],
                        value='DoNothing',
                        inline=True,
                        className='mb-3',
                        style={'margin-right': '10px'},
                        inputClassName='mr-2',
                    )
                ]), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Risk Free Rate:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.Input(id='risk-free-rate', type='number', value=0.04, className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Frequency:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.Dropdown(id='frequency', options=[{'label': 'D', 'value': 'D'}, {'label': 'M', 'value': 'M'}, {'label': 'Y', 'value': 'Y'}], value='M', className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('From Date:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.DatePickerSingle(id='from-date', date='2023-01-01', className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('To Date:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.DatePickerSingle(id='to-date', date='2023-05-10', className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(dbc.Label('Comments:', className='mb-1 text-end'), width=3),
                dbc.Col(dcc.Textarea(id='comments', value='', className='mb-3', style={'width': '100%'}), width=9),
            ]),
            dbc.Row([
                dbc.Col(width=3),
                dbc.Col([
                    dcc.Link(
                    dbc.Button('Submit', id='new-portfolio-submit-button',n_clicks = 0, color='primary', className='mt-3', style={'float': 'right'}),
                    id="report-link",
                    # href="#",
                    href="/reports",
                    ),
                ], width=6),
            ], justify="end"),
        ],md = {'offset' : 1}),
    ], justify="center"),
    html.Div(id='console')
], fluid=True)




def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8',errors='replace')))
        elif 'xlsx' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file.'
        ])
    data = df.to_dict('records')
    return data

@callback(Output('portfolio-data-table', 'data'),
              Input('upload-data', 'contents'),
              State('upload-data', 'filename'),
              State('upload-data', 'last_modified')
              )


def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children = [parse_contents(c, n, d) for c, n, d in zip(list_of_contents, list_of_names, list_of_dates)]
        inner_list = children[0]
        flattened_data = []
        for dictionary in inner_list:
            flattened_data.append(dictionary)
        return flattened_data
    elif  list_of_contents is None:
        df = pd.read_csv("data_processor/tests/test_data/table.csv")
        data = df.to_dict('records')
        return data



@callback(Output('portfolio-data-table', 'data',allow_duplicate=True),
              Input('new-portfolio-submit-button', 'n_clicks'),
              prevent_initial_call=True
        )

def update_output(n_clicks):
    if n_clicks:
        return file_date.dict('records')
    return None


@callback(
    [Output("report-link", "href"),
    Output('load-data-storage', 'data')],
    [Input("new-portfolio-submit-button", "n_clicks")],
    [
        State('portfolio-data-table', 'data'),
        State('portfolio-name', 'value'),
        State('client-id', 'value'),
        State('delete-pickle', 'value'),
        State('simulations', 'value'),
        State('on-conflict', 'value'),
        State('risk-free-rate', 'value'),
        State('frequency', 'value'),
        State('from-date', 'date'),
        State('to-date', 'date'),
        State('comments', 'value'),
        State('data-store', 'data')
    ],
    prevent_initial_call=True
)


def search(n_clicks, portfolio_data_table, portfolio_name, client_id, delete_pickle, simulations, 
           on_conflict, risk_free_rate, frequency, from_date, to_date, comments, data_store):
    if n_clicks:
        load_data_store_count = 1
        if data_store:
            load_data_store_count = data_store.get('count') + 1

        params_data = {
            "PortfolioName": portfolio_name,
            "ClientID": client_id,
            "Delete_pickle": delete_pickle,
            "Simulations": simulations,
            "RiskFreeRate": risk_free_rate,
            "Frequency": frequency,
            "FromDate": from_date,
            "ToDate": to_date,
            "Comments": comments
        }

        working_data = generate_hash_key(portfolio_data_table, params_data)

        hash_exists = check_if_hash_key_exists(working_data['hash_key'])

        if not hash_exists:
            hash_key = simulate_new_profile(working_data)
        else:
            if on_conflict == 'Update':
                hash_key = simulate_new_profile(working_data)
            elif on_conflict == 'DoNothing':
                logging.info('Hash key already exists. Doing nothing.')
                hash_key = working_data['hash_key']

        data = {"hash_key": hash_key,
                    "count": load_data_store_count}
        return "/reports", data
    return dash.no_update