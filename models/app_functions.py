if __name__ == "__main__":
    import sys
    sys.path.append('/Users/jamesmarchetti/Repos/PythonAssetAllocationTool')
import ast
import hashlib
from json import dumps
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import pyodbc

import plotly.express as px
import plotly.graph_objects as go

from database.database_modules import get_dataframe_by_hashkey

import logging

from listner import check_for_updates, process_notification
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# def display_simulated_ef_with_random(response, figsize=(10, 7)):
#     ''' Displays the efficient frontier with the random portfolios
#     :param response: dict
#     :param figsize: tuple
#     :return: fig
#     '''
#     max_sharpe_return = response["max_sharpe"]["return"]
#     max_sharpe_volatility = response["max_sharpe"]["volatility"]
#     max_sharpe_allocation = pd.DataFrame(response["max_sharpe"]["allocation"], index=response["mean_returns"].index, columns=["allocation"])
#     max_sharpe_allocation.allocation = [round(i * 100, 2) for i in max_sharpe_allocation.allocation]
#     max_sharpe_allocation = max_sharpe_allocation.T

#     min_vol_return = response["min_volatility"]["return"]
#     min_vol_volatility = response["min_volatility"]["volatility"]
#     min_vol_allocation = pd.DataFrame(response["min_volatility"]["allocation"], index=response["mean_returns"].index, columns=["allocation"])
#     min_vol_allocation.allocation = [round(i * 100, 2) for i in min_vol_allocation.allocation]
#     min_vol_allocation = min_vol_allocation.T

#     results = response["simulated_portfolios"]
#     efficient_portfolios = response["efficient_portfolios"]

#     fig = go.Figure()
#     fig.add_trace(go.Scatter(x=results[0, :], y=results[1, :], mode="markers", marker=dict(color=results[2, :], colorscale="YlGnBu", showscale=True, colorbar=dict(title="Sharpe ratio")), text=results[2, :], hovertemplate="Volatility: %{x}<br>Returns: %{y}<br>Sharpe Ratio: %{text}<extra></extra>"))
#     fig.add_trace(go.Scatter(x=[max_sharpe_volatility], y=[max_sharpe_return], mode="markers", marker=dict(color="red", size=10, symbol="star"), name="Maximum Sharpe ratio"))
#     fig.add_trace(go.Scatter(x=[min_vol_volatility], y=[min_vol_return], mode="markers", marker=dict(color="green", size=10, symbol="star"), name="Minimum volatility"))

#     target = np.linspace(min_vol_return, results[1, :].max(), 50)
#     fig.add_trace(go.Scatter(x=[p['fun'] for p in efficient_portfolios], y=target, mode="lines", line=dict(color="black", dash="dash"), name="efficient frontier"))

#     fig.update_layout(title="Simulated Portfolio Optimization based on Efficient Frontier", xaxis_title="Annualized Volatility", yaxis_title="Annualized Returns", legend=dict(x=0.05, y=0.95))

#     return fig

import plotly.express as px

def get_dash_table_by_hashkey(hash_key):
    dataframes = get_dataframe_by_hashkey(hash_key)
    tables = []


    if 'monte_carlo' in dataframes:
        monte_carlo_df = dataframes.get('monte_carlo')
        fig = go.Figure()

        # Scatter plot of Monte Carlo simulated portfolios

        #### NOT PLOTTING CORRECTLY #### ATTN:JAMES
        fig.add_trace(go.Scatter(
            x=monte_carlo_df['simulated_stdev'], 
            y=monte_carlo_df['simulated_return'], 
            mode='markers', 
            name='Simulated Portfolios',
            opacity=0.5
        ))

        # If 'other_data' exists in dataframes and it has required columns, plot the efficient frontier
        if 'other_data' in dataframes:
            other_data_df = dataframes.get('other_data')

            # Convert string representations of lists into actual lists
            volatilities = ast.literal_eval(other_data_df['efficient_portfolios_volatilities'][0])
            returns = ast.literal_eval(other_data_df['efficient_portfolios_returns'][0])

            if 'efficient_portfolios_volatilities' in other_data_df.columns and 'efficient_portfolios_returns' in other_data_df.columns:
                fig.add_trace(go.Scatter(
                    x=volatilities, 
                    y=returns, 
                    mode='lines', 
                    name='Efficient Frontier',
                    line=dict(color='blue')
                ))

        # Update layout
        fig.update_layout(
            title='Simulated Portfolio Optimization based on Efficient Frontier',
            xaxis_title='Volatility (Standard Deviation)',
            yaxis_title='Returns',
            autosize=False,
            width=500,
            height=500,
            margin=dict(l=50, r=50, b=100, t=100, pad=4),
            paper_bgcolor="LightSteelBlue",
        )
        tables.append(dcc.Graph(figure=fig))
        del dataframes['monte_carlo']

    for table_name, df in dataframes.items():
        if df is not None and not df.empty:  # Add this line to ensure that the DataFrame is not None and not empty
            # Ensuring the dataframe contains only JSON-serializable data
            df = df.fillna('None')  # Replace NaNs with empty strings
            # Convert datetime objects to strings
            for col in df.columns:
                if df[col].dtype == 'datetime64[ns]':
                    df[col] = df[col].astype(str)
            if '_sa_instance_state' in df.columns:
                df = df.drop(columns=['_sa_instance_state'])
            dict_data = df.to_dict('records')
            table = html.Div([
                html.H3(table_name),
                dash_table.DataTable(
                    id=f'table-{table_name}',
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=dict_data,
                    page_size=10,
                    editable=True,
                    cell_selectable=True,
                    filter_action="native",
                    sort_action="native",
                    style_table={"overflowX": "auto"},
                    row_selectable="multi",
                )
            ])
            tables.append(table)
        
    return tables

def generate_hash_key(data_table, s_params):
    '''Generates a hash key based on the request body and the s_params
    
    Args:
        data_table (dict): The request body
        s_params (dict): The s_params
        
    Returns:
        dict: A dictionary containing the hash key, the stringified request body and the stringified s_params'''
    request_body = data_table
    # request_body = dumps({"ticker":"ADH","quantity":"2352","category":"Australian Equities"})
    logging.info(request_body)
    logging.info(s_params)
    params_list = []
    params_list.append(s_params)
    string_s_params = dumps(params_list)
    string_request_body = dumps(request_body)

    hash_key = hashlib.sha256((string_request_body + string_s_params).encode()).hexdigest()
    logging.info(f"hashKey: {hash_key}")

    return {'hash_key': hash_key, 'string_request_body': string_request_body, 'string_s_params': string_s_params}

def check_if_hash_key_exists(hash_key):
    '''Checks if the hash key exists in the database
    
    Args:
        hash_key (str): The hash key
        
    Returns:
        bool: True if the hash key exists in the database, False otherwise'''
    from models.SQLalchemy import Notification
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import sessionmaker, Session

    results = []

    ###### This code should be moved to a config file ##### ATTN: SHAH
    db_config = {
        'server': 'sayers-wealth-sql01.database.windows.net',
        'user': 'sqladmin',
        'password': 'Qiu4OysDEF9I'
    }

    logging.basicConfig(level=logging.INFO)
    conection_str = f"mssql+pyodbc://{db_config['user']}:{db_config['password']}@{db_config['server']}/sayers-wealth-prd-sqldb?driver=ODBC+Driver+17+for+SQL+Server&MARS_Connection=Yes"

    engine = create_engine(conection_str)

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session: Session = SessionLocal()
    
    # Select all unchecked notifications
    query = select(Notification).where(Notification.uniqueID == hash_key)
    result = session.execute(query).scalars().all()
    session.close()

    if len(result) > 0:
        return True
    else:
        return False

def simulate_new_profile(data):
    '''Simulates a new profile based on the request body
    
    Args:
        data (dict): The request body
        
    Returns:
        dict: A dictionary containing the hash key, the stringified request body and the stringified s_params'''
    
    #graph_data_list = []
    # s_params = dumps({"PortfolioName":"TestPortfolio-TESTINGAFTERBREAK","ClientID":"1099","OnConflict":"Update"})
    connection_string = (
    r'Driver={ODBC Driver 17 for SQL Server};'
    r'Server=sayers-wealth-sql01.database.windows.net;'
    r'Database=sayers-wealth-prd-sqldb;'
    r'UID=sqladmin;'
    r'PWD=Qiu4OysDEF9I;'
    )
    logging.info(connection_string)

    hash_key, string_request_body, string_s_params = data['hash_key'], data['string_request_body'], data['string_s_params']

    # request_body = data_table
    # # request_body = dumps({"ticker":"ADH","quantity":"2352","category":"Australian Equities"})
    # logging.info(request_body)
    # logging.info(s_params)
    # params_list = []
    # params_list.append(s_params)
    # string_s_params = dumps(params_list)
    # string_request_body = dumps(request_body)

    # hash_key = hashlib.sha256((string_request_body + string_s_params).encode()).hexdigest()
    # logging.info(f"hashKey: {hash_key}")

    inserted_ids = ""
    with pyodbc.connect(connection_string) as con:
        with con.cursor() as cursor:
            logging.info("Before hitting the uspAssetallocationHoldings..")
            cursor.execute("EXEC uspAssetallocationHoldings @JsonData=?, @Params=?, @HashKey=?",(string_request_body, string_s_params, hash_key))
            logging.info("After hitting the uspAssetallocationHoldings..")
            rows = cursor.fetchall()
            for row in rows:
                inserted_ids = row.InsertedIDs
    logging.info("Before hitting the check for updates..")
    check_for_updates(hash_key)
    logging.info(hash_key)
    return hash_key

def display_simulated_ef_with_random(response, figsize=(10, 7)):
    ''' Displays the efficient frontier with the random portfolios
    :param response: dict
    :param figsize: tuple
    :return: fig
    '''
    max_sharpe_return = response["max_sharpe"]["return"]
    max_sharpe_volatility = response["max_sharpe"]["volatility"]
    max_sharpe_allocation = pd.DataFrame(response["max_sharpe"]["allocation"], index=response["mean_returns"].index, columns=["allocation"])
    max_sharpe_allocation.allocation = [round(i * 100, 2) for i in max_sharpe_allocation.allocation]
    max_sharpe_allocation = max_sharpe_allocation.T

    min_vol_return = response["min_volatility"]["return"]
    min_vol_volatility = response["min_volatility"]["volatility"]
    min_vol_allocation = pd.DataFrame(response["min_volatility"]["allocation"], index=response["mean_returns"].index, columns=["allocation"])
    min_vol_allocation.allocation = [round(i * 100, 2) for i in min_vol_allocation.allocation]
    min_vol_allocation = min_vol_allocation.T

    results = response["simulated_portfolios"]
    efficient_portfolios = response["efficient_portfolios"]

    fig = px.scatter(results.T, 
                     x=0, y=1, 
                     color=2, 
                     color_continuous_scale="YlGnBu", 
                     hover_data=[2], 
                     labels={'0': 'Volatility', '1': 'Returns'}, 
                     title="Simulated Portfolio Optimization based on Efficient Frontier")
    
    fig.add_trace(px.scatter(x=[max_sharpe_volatility], y=[max_sharpe_return], color_discrete_sequence=['red'], size=[3], symbol=['star']).data[0])
    fig.add_trace(px.scatter(x=[min_vol_volatility], y=[min_vol_return], color_discrete_sequence=['green'], size=[3], symbol=['star']).data[0])

    target = np.linspace(min_vol_return, results[:,1].max(), 50)
    fig.add_trace(px.line(x=[p['fun'] for p in efficient_portfolios], y=target, color_discrete_sequence=['black'], line_dash=["dash"]*50).data[0])
    fig.update_layout(legend=dict(x=0.05, y=0.95))
    return fig

    # fig = px.scatter(results.T, 
    #                  x=0, y=1, 
    #                  color=2, 
    #                  color_continuous_scale="YlGnBu", 
    #                  hover_data=[2], 
    #                  labels={'0': 'Volatility', '1': 'Returns'}, 
    #                  title="Simulated Portfolio Optimization based on Efficient Frontier")
    # # Add the efficient frontier as a line trace to the scatter plot
    # efficient_frontier = go.Scatter(x=[p['fun'] for p in efficient_portfolios],
    #                                 y=[p['fun'] for p in efficient_portfolios],
    #                                 mode='lines',
    #                                 name='Efficient Frontier',
    #                                 line=dict(color='red', width=2))
    # fig.add_trace(efficient_frontier)
    # fig.update_layout(legend=dict(x=0.05, y=0.95))
    # return fig


def create_table(df):
    ''' Create a Dash datatable from a Pandas dataframe and add selection features.
    
    Args:
        df (pd.DataFrame): Pandas dataframe to be converted to a Dash datatable.
        
    Returns:
        html.Div: Dash datatable.
    '''
    return html.Div(
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

def get_asset_allocation(response):
    """
    Returns a pie chart with the asset allocation for each optimized portfolio.
    """
    allocation = response['max_sharpe']['allocation']
    tickers = response['mean_returns'].index
    fig = go.Figure(data=[go.Pie(labels=tickers, values=allocation)])
    fig.update_layout(title='Asset Allocation - Max Sharpe Ratio Portfolio')
    return fig

def get_heatmap(response):
    """
    Returns a heatmap of the covariance matrix to show the correlation between each pair of assets in the portfolio.
    """
    fig = go.Figure(data=go.Heatmap(
            z=response['cov_matrix'],
            x=response['mean_returns'].index,
            y=response['mean_returns'].index,
            colorscale='Viridis'))
    fig.update_layout(title='Covariance Matrix Heatmap')
    return fig

def get_returns_chart(result_dict):
    """
    Returns a line chart with the mean returns for each asset in the portfolio.
    """
    returns = result_dict['mean_returns']
    fig = px.line(x=returns.index, y=returns.values)
    fig.update_layout(title='Mean Returns for Each Asset')
    return fig

import numpy as np

def get_allocations_bar_chart(response: pd.DataFrame):
    """
    Returns a bar chart showing the allocations for each asset in the optimized portfolios.
    """

    allocations = response['quantity'].to_numpy()
    tickers = response['ticker']

    data = []
    for i, (allocation, ticker) in enumerate(zip(allocations, tickers)):
        trace = go.Bar(x=['Max Sharpe', 'Min Volatility'], y=[allocation, allocation], name=ticker)
        data.append(trace)

    layout = go.Layout(title='Asset Allocations for Optimized Portfolios',
                       xaxis={'title': 'Portfolio Type'},
                       yaxis={'title': 'Allocation'},
                       barmode='group')

    fig = go.Figure(data=data, layout=layout)

    return fig

def get_table(response):
    """
    Returns a table with the returns, volatility, and allocation for each of the optimized portfolios.
    """
    portfolio_types = ['max_sharpe', 'min_vol']
    portfolio_data = []
    for portfolio_type in portfolio_types:
        portfolio = response[1][portfolio_type]
        portfolio_data.append([portfolio_type, portfolio['returns'], portfolio['volatility'], portfolio['weights']])
    fig = go.Figure(data=[go.Table(
            header=dict(values=['Portfolio Type', 'Expected Return', 'Volatility', 'Asset Allocation']),
            cells=dict(values=[portfolio_data[i] for i in range(len(portfolio_data))]))
        ])
    return fig


if __name__ == "__main__":
    test_hash = '966326d51effc22653a91de933195142dad37107f58dc1f9d40f348edc4473fa'
    dataframes = get_dataframe_by_hashkey(test_hash)
    print(dataframes)