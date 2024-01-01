# import sys
# sys.path.append(r'post-holdings\\')
# Get the current working directory
import os
cwd = os.getcwd()

from typing import List
import pandas as pd
import json
import numpy as np
from datetime import datetime

from api.function_ds_extract_price import get_datastream, run_pipeline

def find_freq(price_data: pd.DataFrame) -> str:
    '''Find the frequency of the price data.'''''
    dates = list(price_data.index)
    try:
        freq_days = (pd.to_datetime(dates[1]) - pd.to_datetime(dates[0])).days
        if freq_days == 1:
            freq = 'D'
        elif freq_days == 7:
            freq = 'W'
        elif freq_days in [30, 31, 28]:
            freq = 'M'
        else:
            freq = 'D'
    except:
        freq = 'D'
    return freq.upper()


def get_oldest_date(price_data:pd.DataFrame) -> datetime:
    '''Find the oldest date in the price data.'''
    oldest_date = price_data.index[0]
    for col in price_data.columns[1:]:
        oldest_date = min(oldest_date, price_data[col].dropna().index[0])
    return oldest_date

def convert_into_yearly_timedelta(freq:str) -> pd.Timedelta:
    '''Convert the frequency into a yearly timedelta.'''
    if freq == 'D':
        return pd.Timedelta(365, unit='D')
    elif freq == 'W':
        return pd.Timedelta(52, unit='W')
    elif freq == 'M':
        return pd.Timedelta(12, unit='M')
    else:
        raise ValueError(f"Frequency {freq} is not supported.")
    

def find_the_start_end_input(price_data: pd.DataFrame, freq: str, start: str, end: str) -> str:
    '''Find the end date for the price data.'''
    dates = list(price_data.index)
    option_1 = datetime.strptime(dates[-1],"%Y-%m-%d") if dates[-1] != 'Dates' else datetime.strptime(dates[-2],"%Y-%m-%d")
    option_2 = datetime.strptime(dates[0],"%Y-%m-%d") if dates[0] != 'Dates' else datetime.strptime(dates[1],"%Y-%m-%d")
    if option_1 > option_2:
        end = option_1 if end == None else end
        start = option_2 if start == None else start
    else:
        end = option_2 if end == None else end
        start = option_1 if start == None else start

    return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

def merge_dfs(price_data: pd.DataFrame, market_returns: pd.DataFrame, holding_data: pd.DataFrame) -> pd.DataFrame:
    '''Merge the price data and market returns data.'''
    asset_returns = price_data.pct_change().dropna(how='all')
 
    holding_data = holding_data.reset_index(drop=True) if holding_data.index.name == 'name' else holding_data

    market_returns = market_returns.xs('PI(AUD)', level=1, axis=1)
    asset_returns = asset_returns.xs('PI(AUD)', level=1, axis=1)

    asset_returns = asset_returns.apply(pd.to_numeric, errors='coerce')
    market_returns = market_returns.apply(pd.to_numeric, errors='coerce')

    return pd.merge(asset_returns, market_returns, left_index=True, right_index=True, how='outer')


def calculate_betas(price_data: pd.DataFrame, market_returns: pd.DataFrame, merge_dfs: list, mapping: dict, holding_data: pd.DataFrame) -> pd.DataFrame:
    '''Calculate the betas for the holdings data.'''
    betas = {}
    for row in holding_data.itertuples():
        for asset in price_data.columns:
            if row.ticker in asset[0]:
                asset_benchmark = mapping.get(row.category)
                temp_merged_df = merge_dfs[[asset[0],asset_benchmark['code']]].copy().dropna()
                covariance = temp_merged_df[asset[0]].cov(temp_merged_df[asset_benchmark['code']])
                variance = temp_merged_df[asset_benchmark['code']].var()
                
                beta = covariance / variance
                if np.isnan(beta): beta = 1.0

                if asset[0] not in betas:
                    betas[asset[0]+"|"+asset_benchmark['code']] = beta
    return betas

def get_asset_prices(holdings_data: pd.DataFrame, fields: list, start: str, batch_size: int, freq: str) -> pd.DataFrame:
    '''Get the asset prices for the holdings data.'''
    from function_validator import RefinitivCodeValidator
    validator = RefinitivCodeValidator(holdings_data)
    validator.assign_refinitiv_code(validator.df)
    price_data = run_pipeline(validator.asset_list, fields, start=start, batch_size=batch_size, freq=freq) # <<------= REMOVE
    return price_data[0]

def market_returns(holdings_data: pd.DataFrame, price_data: pd.DataFrame, start: str, end: str, fields: list = ['X(PI)~AUD'], batch_size=25) -> pd.DataFrame:
    '''Get the market returns for the holdings data.
    If the holdings data has a benchmark column, then use that to get the market returns.
    If the holdings data does not have a benchmark column, then use the category column to get the market returns.
    If the holdings data does not have a category column, then use the mapping.json file to get the market returns.
    '''
    if not isinstance(price_data, pd.DataFrame): price_data = pd.DataFrame() if price_data == None else pd.DataFrame(price_data)
    price_data = get_asset_prices(holdings_data, fields, start, batch_size, freq = "M") if price_data.empty else price_data
    freq = find_freq(price_data)
    start, end = find_the_start_end_input(price_data, freq, start, end) if start == None and end == None else (start, end)
    #price_data.to_json(r'postholdings\data\raw\price_data.json')
    # if 'benchmark' in holdings_data.columns:
    #     unique_benchmarks = holdings_data['benchmark'].unique()
    #     response = get_datastream(unique_benchmarks, ['X(PI)~AUD'], start, end, 25, freq)

    if 'category' in holdings_data:
        with open(cwd + r'/data/raw/mapping.json', 'r') as f:
            mapping = json.load(f)
    unique_benchmarks = list(set([mapping[cat]['code'] for cat in holdings_data['category'] if cat in mapping]))
    #response, _ = run_pipeline(input_list=unique_benchmarks, fields=['X(PI)~AUD'], start=start, end=end, freq=freq, batch_size=25)
    response = get_datastream(unique_benchmarks, ['X(PI)~AUD'], start, end, 25, freq)
        
    # else:
    #     raise ValueError('No benchmark or category in the holdings data.')

    market_returns = response.pct_change().dropna(how='all')

    return market_returns, mapping, price_data, start, end


def fill_missing_values(merged_dfs: pd.DataFrame, betas: dict) -> pd.DataFrame:
    '''Fill in the missing values in the price data.'''
    filled_price_data = merged_dfs.copy()
    
    for name_beta, beta in betas.items():
        asset, market_return_col = name_beta.split("|")
        
        market_returns = filled_price_data[market_return_col] * beta
        filled_price_data[asset] = filled_price_data[asset].fillna(market_returns)
    
    return filled_price_data, betas

def fill_in_missing_returns(holdings_data: pd.DataFrame, price_data: pd.DataFrame = None, start: str = None, end: str = None) -> pd.DataFrame:
    '''Fill in the missing dates in the price data.'''
    holdings_data = pd.DataFrame() if holdings_data == None else pd.DataFrame(holdings_data)
    # holdings_data.to_json(r'postholdings\data\raw\holding_data.json')
    # price_data.to_json(r'postholdings\data\raw\price_data.json')

    market_returns_df, mapping, price_data, start, end = market_returns(holdings_data, price_data, start, end)
    merged_dfs = merge_dfs(price_data, market_returns_df, holdings_data)
    df_betas = calculate_betas(price_data, market_returns_df, merged_dfs, mapping, holdings_data)
    start, end = start, end if start != "" and end != "" or start != None and end != None else (merged_dfs.index[0], merged_dfs.index[-1])
    filled_price_data, betas = fill_missing_values(merged_dfs, df_betas)
    return filled_price_data, betas, start, end

if __name__ == '__main__':

    holding_data = pd.read_csv(r"C:\Users\sayersqvm\Documents\Python_Scripts\AssetAllocationTool\data_processor\tests\test_data\table.csv", index_col=0)
    
    with open(r"C:\Users\sayersqvm\Documents\Python_Scripts\AssetAllocationTool\data_processor\tests\test_data\sample_metadata_dict.txt", "r") as f:  
        metadata_dict = eval(f.read())
    from api.function_ds_extract_price import run_pipeline
    
    result = fill_in_missing_returns(holding_data, price_data = None, start = "", end = "")
    
    pass