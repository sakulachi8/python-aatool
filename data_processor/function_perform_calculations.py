import logging, json, os , warnings
import numpy as np
import pandas as pd

from scipy.optimize import minimize
from scipy.stats import skew, kurtosis

from models.SQLalchemy import Notification, MonteCarlo, PortfolioReturns, MarketReturns, OtherData, Holdings
from database.database_modules import load_results_to_database

# Use the 'warnings' library to suppress the warning
with warnings.catch_warnings():
    warnings.filterwarnings('ignore', category=RuntimeWarning)


def portfolio_annualized_performance(weights, mean_returns, cov_matrix, freq='D'):
    if freq == 'D':
        returns = np.sum(mean_returns * weights) * 252
        std_dev = np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(252)
    elif freq == 'M':
        returns = np.sum(mean_returns * weights) * 12
        std_dev = np.sqrt(weights.T @ cov_matrix @ weights) * np.sqrt(12)
    elif freq == 'Y':
        returns = np.sum(mean_returns * weights)
        std_dev = np.sqrt(weights.T @ cov_matrix @ weights)
    else:
        raise ValueError("Invalid frequency: '{}'. The frequency must be 'D', 'M', or 'Y'.".format(freq))
    return std_dev, returns


def neg_sharpe_ratio(weights, mean_returns, cov_matrix, risk_free_rate, freq):
    p_var, p_ret = portfolio_annualized_performance(weights, mean_returns, cov_matrix, freq)
    return -(p_ret - risk_free_rate) / p_var

def optimize_portfolio(objective_function, mean_returns, cov_matrix, *args) -> pd.DataFrame:
    num_assets = len(mean_returns)
    constraints = {'type': 'eq', 'fun': lambda x: np.sum(x) - 1}
    bounds = tuple((0, 1) for asset in range(num_assets))
    result = minimize(objective_function, num_assets * [1. / num_assets], args=(mean_returns, cov_matrix, *args), bounds=bounds, constraints=constraints)
    return result

def max_sharpe_ratio(mean_returns, cov_matrix, risk_free_rate, freq):
    return optimize_portfolio(neg_sharpe_ratio, mean_returns, cov_matrix, risk_free_rate, freq)

def min_variance(mean_returns, cov_matrix, freq):
    return optimize_portfolio(lambda w, *args: portfolio_annualized_performance(w, *args)[0], mean_returns, cov_matrix, freq)

def efficient_frontier(mean_returns, cov_matrix, returns_range, freq='D'):
    efficient_portfolios = [minimize(lambda w, *args: portfolio_annualized_performance(w, *args, freq=freq)[0], len(mean_returns) * [1. / len(mean_returns)], args=(mean_returns, cov_matrix), bounds=tuple((0, 1) for _ in range(len(mean_returns))), constraints=({'type': 'eq', 'fun': lambda x: portfolio_annualized_performance(x, mean_returns, cov_matrix, freq=freq)[1] - ret}, {'type': 'eq', 'fun': lambda x: np.sum(x) - 1})) for ret in returns_range]

    ef_returns = [portfolio_annualized_performance(p.x, mean_returns, cov_matrix, freq=freq)[1] for p in efficient_portfolios]
    ef_volatilities = [np.sqrt(portfolio_annualized_performance(p.x, mean_returns, cov_matrix, freq=freq)[0]) for p in efficient_portfolios]

    return efficient_portfolios, ef_returns, ef_volatilities



# def treynor_ratio(portfolio_returns, risk_free_rate, market_returns, beta=1): # fix this one - beta shouldnt be 1
#     return (portfolio_returns - risk_free_rate) / 1(portfolio_returns, market_returns)

# def jensens_alpha(portfolio_returns, risk_free_rate, market_returns, beta =1): # fix this - beta shouldnt be 1
#     return portfolio_returns - (risk_free_rate + 1(portfolio_returns, market_returns) * (market_returns - risk_free_rate))


def sortino_ratio(portfolio_returns, risk_free_rate, target=0):
    '''Compute the Sortino ratio of a portfolio given the portfolio returns, risk-free rate, and target return.
    The Sortino ratio is a variation of the Sharpe ratio that differentiates harmful volatility from total overall volatility
    by using the asset's standard deviation of negative asset returns, called downside deviation, 
    instead of the total standard deviation of asset returns.'''
    return (portfolio_returns - risk_free_rate) / downside_risk(portfolio_returns, target)

def downside_risk(portfolio_returns, target=0):
    '''Compute the downside risk of a portfolio given the portfolio returns and target return.
    The downside risk is defined as the standard deviation of the returns that are less than the target return.
    '''
    if isinstance(portfolio_returns, np.ndarray):
        downside_diff = portfolio_returns - target
        squared_diff = downside_diff * (downside_diff < 0)  # only consider differences where portfolio_return < target
        return np.sqrt(np.mean(squared_diff ** 2))
    else:
        return 0 if portfolio_returns >= target else portfolio_returns - target


def information_ratio(portfolio_returns, benchmark_returns):
    return np.mean(portfolio_returns - benchmark_returns) / np.std(portfolio_returns - benchmark_returns, ddof=1)

# def alpha(portfolio_returns, risk_free_rate, benchmark_returns):
#     return portfolio_returns - (risk_free_rate + beta(portfolio_returns, benchmark_returns) * (benchmark_returns - risk_free_rate))

def sharpe_ratio(portfolio_returns, risk_free_rate):
    return (portfolio_returns - risk_free_rate) / np.std(portfolio_returns, ddof=1)

def omega_ratio(portfolio_returns, risk_free_rate, target=0):
    return (portfolio_returns - target) / downside_risk(portfolio_returns, target)

# def calc_portfolio_perf(weights, mean_returns, cov_matrix, risk_free_rate):
#     portfolio_std_dev, portfolio_return = portfolio_annualized_performance(weights, mean_returns, cov_matrix, freq)
#     sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_std_dev
#     return portfolio_std_dev, portfolio_return, sharpe_ratio

def monte_carlo_simulation(num_portfolios, mean_returns, cov_matrix, risk_free_rate, freq):
    results = np.zeros((3, num_portfolios))
    weights_record = []
    for i in range(num_portfolios):
        weights = np.random.random(len(mean_returns))
        weights /= np.sum(weights)
        weights_record.append(weights)
        portfolio_std_dev, portfolio_return = portfolio_annualized_performance(weights, mean_returns, cov_matrix, freq)
        results[0, i] = portfolio_std_dev #volatility/risk
        results[1, i] = portfolio_return # returns of each portfolio simulated
        results[2, i] = (portfolio_return - risk_free_rate) / portfolio_std_dev # sharpe ratio
    return results, weights_record

def max_drawdown(price_data: pd.DataFrame):
    '''Compute the maximum drawdown of a portfolio given the price data of the portfolio.
    The maximum drawdown is defined as the maximum loss from a peak to a trough of a portfolio, 
    before a new peak is attained.
    '''
    price_data.reindex(pd.to_datetime(price_data.index))
    cumulative_returns = (1 + price_data.pct_change()).cumprod()
    max_return = cumulative_returns.expanding().max()
    drawdowns = (cumulative_returns - max_return) / max_return
    return drawdowns.min()

def portfolio_skewness_kurtosis(weights, returns_data):
    '''Compute the skewness and kurtosis of a portfolio given the weights of assets in the portfolio.'''
    portfolio_returns = np.dot(returns_data, weights)
    return skew(portfolio_returns), kurtosis(portfolio_returns)

def diversification_index(weights):
    '''Compute the diversification index given the weights of assets in a portfolio.
    The diversification index is defined as the inverse of the Herfindahl-Hirschman Index (HHI).
    The HHI is computed as the sum of the squared weights of the assets in the portfolio.
    The diversification index is computed as the inverse of the HHI.
    '''
    hhi = np.sum(weights**2)
    div_index = 1 / hhi
    return div_index


def main(returns_benchmark_data: pd.DataFrame, timeseries_df, risk_free_rate, num_portfolios, metadata_dict, holdings_data, start, end, freq, betas:dict, uniqueID, missing_data, comments) -> dict:
    '''Main function for the portfolio optimization API.
    The function takes in the price data of the assets in the portfolio, the risk-free rate, the number of portfolios to simulate,
    and the type of request.

    For an efficient frontier scatter plot, 
        call main(price_data, risk_free_rate, num_portfolios, "efficient_frontier_scatter").
    For data and analysis on a specific portfolio, 
        call main(price_data, risk_free_rate, num_portfolios, "portfolio_analysis", [portfolio_weights]).
    For data and analysis on two competing portfolios, 
        call main(price_data, risk_free_rate, num_portfolios, "competing_portfolios", [portfolio1_weights, portfolio2_weights]).'''
    if returns_benchmark_data.empty:
        return {"message": "Please provide valid time series data."}

    print('Building portfolio analysis data...')
    key_to_split = list(betas.keys())
    returns_columns = list(set([key.split('|')[0] for key in key_to_split]))
    market_returns_columns = list(set([key.split('|')[1] for key in key_to_split]))

    portfolio_returns_data = returns_benchmark_data[returns_columns]
    market_returns = returns_benchmark_data[market_returns_columns]

    portfolio_mean_returns = portfolio_returns_data.mean()
    portfolio_cov_matrix = portfolio_returns_data.cov()

    results, weights_record = monte_carlo_simulation(num_portfolios, portfolio_mean_returns, portfolio_cov_matrix, risk_free_rate, freq)
    # results have the following format:
    # results[0, :] = portfolio_std_dev
    # results[1, :] = portfolio_return
    # results[2, :] = sharpe_ratio

    max_sharpe_portfolio_weights = max_sharpe_ratio(portfolio_mean_returns, portfolio_cov_matrix, risk_free_rate, freq)
    sdp_max_sharpe, rp_max_sharpe = portfolio_annualized_performance(max_sharpe_portfolio_weights.x, portfolio_mean_returns, portfolio_cov_matrix, freq)
    min_vol_portfolio_weights = min_variance(portfolio_mean_returns, portfolio_cov_matrix, freq)
    sdp_min_vol, rp_min_vol = portfolio_annualized_performance(min_vol_portfolio_weights.x, portfolio_mean_returns, portfolio_cov_matrix, freq)

    max_target_return = results[1, :].max()
    returns_range = np.linspace(rp_min_vol, max_target_return, 50)
    efficient_portfolios, ef_returns, ef_volatilities = efficient_frontier(portfolio_mean_returns, portfolio_cov_matrix, returns_range)

    max_drawdown_resp = max_drawdown(timeseries_df)
    max_drawdown_resp_reindexed = max_drawdown_resp.reset_index()
    max_drawdown_resp_dict = max_drawdown_resp_reindexed.to_dict(orient="records")
    #portfolio_analysis_data = [portfolio_analysis(p, portfolio_mean_returns, portfolio_cov_matrix, portfolio_returns_data, None, risk_free_rate, None, timeseries_df) for p in portfolios]

    analytics = {"max_sharpe": {
                    "weights": json.dumps(max_sharpe_portfolio_weights.x.tolist()),
                    "returns": rp_max_sharpe,
                    "volatility": sdp_max_sharpe},
                "min_vol": {
                    "weights": json.dumps(min_vol_portfolio_weights.x.tolist()),
                    "returns": rp_min_vol,
                    "volatility": sdp_min_vol},
                "efficient_frontier": {
                    "max_target_return": max_target_return,
                    "returns_range": json.dumps(returns_range.tolist())},
                "efficient_portfolios": {
                    "returns": json.dumps(ef_returns),
                    "volatilities": json.dumps(ef_volatilities),  
                    "simulated_returns": json.dumps(results[1, :].tolist()),
                    "simulated_volatilities": json.dumps(results[0, :].tolist()),
                    "weights": json.dumps([portfolio.x.tolist() for portfolio in efficient_portfolios])},
                "max_drawdown": json.dumps(max_drawdown_resp_dict),
                "betas": json.dumps(betas),
                "metadata": json.dumps(metadata_dict),
                "start": start,
                "end": end,
                "freq": freq,
                "uniqueID": uniqueID,
                "portfolio_returns_columns": json.dumps(returns_columns),
                "market_returns_columns": json.dumps(market_returns_columns),
                "risk_free_rate": float(risk_free_rate),
                "num_portfolios": int(num_portfolios),
                "missing_data": json.dumps(missing_data),
                "returns_data": portfolio_returns_data,
                "market_returns": market_returns,
                "returns_columns_raw": returns_columns,
                "market_returns_columns_raw": market_returns_columns,
                "comments": comments,
                "holdings_data": json.dumps(holdings_data)
                }                 

    analytics_to_return = {"max_sharpe": {
                    "weights": max_sharpe_portfolio_weights.x.tolist(),
                    "returns": rp_max_sharpe,
                    "volatility": sdp_max_sharpe},
                "min_vol": {
                    "weights": min_vol_portfolio_weights.x.tolist(),
                    "returns": rp_min_vol,
                    "volatility": sdp_min_vol},
                "efficient_frontier": {
                    "max_target_return": max_target_return,
                    "returns_range": returns_range.tolist()},
                "efficient_portfolios": {
                    "simulated_returns": results[1, :].tolist(),
                    "simulated_volatilities": results[0, :].tolist(),
                    "ef_returns": ef_returns,
                    "ef_volatilities": ef_volatilities,   
                    "weights": [portfolio.x.tolist() for portfolio in efficient_portfolios]},
                "max_drawdown": max_drawdown_resp_dict,
                "betas": betas,
                "metadata": metadata_dict,
                "start": start,
                "end": end,
                "freq": freq,
                "uniqueID": uniqueID,
                "portfolio_returns_columns": returns_columns,
                "market_returns_columns": market_returns_columns,
                "risk_free_rate": float(risk_free_rate),
                "num_portfolios": int(num_portfolios),
                "missing_data": missing_data,
                "returns_data": portfolio_returns_data,
                "market_returns": market_returns,
                "returns_columns_raw": returns_columns,
                "market_returns_columns_raw": market_returns_columns,
                "comments": comments,
                "holdings_data": holdings_data
                }    

    # Prepare the results and weights for loading into the database
    results_data = results.T
    weights_data = weights_record

    # Call the function to load the results into the database
    load_results_to_database(results_data, weights_data, analytics)

    return results_data, weights_data, analytics_to_return, {"message": "Results loaded into the database successfully."}
