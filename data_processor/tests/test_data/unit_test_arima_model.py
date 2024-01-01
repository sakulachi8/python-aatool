from datetime import datetime, timedelta
import numpy as np
import pandas as pd

# Creating the date range
dates = pd.date_range(start="2023-01-01", end="2023-07-01")

# Creating random close prices for three assets
np.random.seed(0)  # For reproducibility
TSLA_prices = np.random.rand(len(dates)) * 300 + 500  # Random prices between 500 and 800
AAPL_prices = np.random.rand(len(dates)) * 50 + 150   # Random prices between 150 and 200
GOOGL_prices = np.random.rand(len(dates)) * 500 + 1000  # Random prices between 1000 and 1500

# Creating the DataFrame
data = pd.DataFrame({
    "TSLA": TSLA_prices,
    "AAPL": AAPL_prices,
    "GOOGL": GOOGL_prices
}, index=dates)

# Creating the weights dictionary
asset_weights = {
    "TSLA": 0.4,
    "AAPL": 0.3,
    "GOOGL": 0.3
}