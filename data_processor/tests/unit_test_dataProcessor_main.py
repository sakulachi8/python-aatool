import unittest
import numpy as np
import pandas as pd
import sys
sys.path.append(r'post-holdings\\')
from function_perform_calculations import main

class TestPortfolioAnalysis(unittest.TestCase):

    def test_main_function(self):
        holding_data = pd.read_csv(r"C:\Users\sayersqvm\Documents\Python_Scripts\AssetAllocationTool\data_processor\tests\test_data\table.csv", index_col=0)
        timeseries_df = pd.read_csv(r"C:\Users\sayersqvm\Documents\Python_Scripts\AssetAllocationTool\data_processor\tests\test_data\sample_timeseries_df.csv", index_col=0, parse_dates=True)
        
        with open(r"C:\Users\sayersqvm\Documents\Python_Scripts\AssetAllocationTool\data_processor\tests\test_data\sample_metadata_dict.txt", "r") as f:  
            metadata_dict = eval(f.read())

        risk_free_rate = 0.01
        num_portfolios = 1000

        # Test efficient frontier scatter plot request
        result1 = main(timeseries_df, holding_data, risk_free_rate, num_portfolios, "efficient_frontier_scatter")
        assert "efficient_frontier_scatter" in result1
        assert "x" in result1["efficient_frontier_scatter"]
        assert "y" in result1["efficient_frontier_scatter"]
        assert len(result1["efficient_frontier_scatter"]["x"]) == 50
        assert len(result1["efficient_frontier_scatter"]["y"]) == 50

        # Test portfolio analysis request
        portfolio_weights = [0.2, 0.3, 0.5]
        result2 = main(timeseries_df, holding_data, risk_free_rate, num_portfolios, "portfolio_analysis", [portfolio_weights])
        assert "portfolio_analysis" in result2
        assert "Annualized Return" in result2["portfolio_analysis"]
        assert "Annualized Volatility" in result2["portfolio_analysis"]
        assert "Sortino Ratio" in result2["portfolio_analysis"]
        assert "Treynor Ratio" in result2["portfolio_analysis"]
        assert "Jensen's Alpha" in result2["portfolio_analysis"]
        assert "Max Drawdown" in result2["portfolio_analysis"]
        assert "Skewness" in result2["portfolio_analysis"]
        assert "Kurtosis" in result2["portfolio_analysis"]
        assert "Diversification Index" in result2["portfolio_analysis"]
        assert "Correlation Matrix" in result2["portfolio_analysis"]
        assert len(result2["portfolio_analysis"]) == 9

        # Test competing portfolios request
        portfolio_weights1 = [0.2, 0.3, 0.5]
        portfolio_weights2 = [0.3, 0.3, 0.4]
        result3 = main(timeseries_df, holding_data, risk_free_rate, num_portfolios, "competing_portfolios", [portfolio_weights1, portfolio_weights2])
        assert "competing_portfolios" in result3
        assert len(result3["competing_portfolios"]) == 2
        assert "Annualized Return" in result3["competing_portfolios"][0]
        assert "Annualized Volatility" in result3["competing_portfolios"][0]
        assert "Sortino Ratio" in result3["competing_portfolios"][0]
        assert "Treynor Ratio" in result3["competing_portfolios"][0]
        assert "Jensen's Alpha" in result3["competing_portfolios"][0]
        assert "Max Drawdown" in result3["competing_portfolios"][0]
        assert "Skewness" in result3["competing_portfolios"][0]
        assert "Kurtosis" in result3["competing_portfolios"][0]
        assert "Diversification Index" in result3["competing_portfolios"][0]
        assert "Correlation Matrix" in result3["competing_portfolios"][0]
        assert len(result3["competing_portfolios"][0]) == 9
        assert "Annualized Return" in result3["competing_portfolios"][1]
        assert "Annualized Volatility" in result3["competing_portfolios"][1]
        assert "Sortino Ratio" in result3["competing_portfolios"][1]
        assert "Treynor Ratio" in result3["competing_portfolios"][1]
        assert "Jensen's Alpha" in result3["competing_portfolios"][1]
        assert "Max Drawdown" in result3["competing_portfolios"][1]
        assert "Skewness" in result3["competing_portfolios"][1]
        assert "Kurtosis" in result3["competing_portfolios"][1]
        assert "Diversification Index" in result3["competing_portfolios"][1]
        assert "Correlation Matrix" in result3["competing_portfolios"][1]
        assert len(result3["competing_portfolios"][1]) == 9


if __name__ == '__main__':
    unittest.main()
