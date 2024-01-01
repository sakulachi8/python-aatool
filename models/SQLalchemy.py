from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy import Column, Integer, Float, String, Date
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Holdings(Base):
    __tablename__ = 'holdings'
    __table_args__ = {'schema': 'assetallocation'}

    uniqueID = Column(String(100), primary_key=True)
    ticker = Column(String(100), nullable=False)
    quantity = Column(Numeric(18, 4), nullable=False)
    category = Column(Numeric(18, 4), nullable=False)
    completed = Column(Integer, nullable=False)
    updated_at = Column(DateTime, nullable=False, server_default=func.now())

class Notification(Base):
    __tablename__ = 'notifications'
    __table_args__ = {'schema': 'assetallocation'}

    uniqueID = Column(String(100), primary_key=True)
    status = Column(Integer, nullable=False)
    clientID = Column(String, nullable=True)
    params = Column(String, nullable=True)


class MonteCarlo(Base):
    __tablename__ = 'monte_carlo'
    __table_args__ = {'schema': 'assetallocation'}

    id = Column(Integer, primary_key=True)
    uniqueID = Column(String)
    simulation_number = Column(Integer)
    simulated_stdev = Column(Float)
    simulated_return = Column(Float)
    simulated_sharpe = Column(Float)
    simulation_weight = Column(String)

    def __init__(self, uniqueID, simulation_number, simulated_stdev, simulated_return, simulated_sharpe, simulation_weight):
        self.uniqueID = uniqueID
        self.simulation_number = simulation_number
        self.simulated_stdev = simulated_stdev
        self.simulated_return = simulated_return
        self.simulated_sharpe = simulated_sharpe
        self.simulation_weight = simulation_weight

class PortfolioReturns(Base):
    __tablename__ = 'portfolio_returns'
    __table_args__ = {'schema': 'assetallocation'}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    uniqueID = Column(String)
    asset = Column(String)
    value = Column(Float)

    def __init__(self, date, uniqueID, asset, value):
        self.date = date
        self.uniqueID = uniqueID
        self.asset = asset
        self.value = value

class MarketReturns(Base):
    __tablename__ = 'market_returns'
    __table_args__ = {'schema': 'assetallocation'}

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    uniqueID = Column(String)
    asset = Column(String)
    value = Column(Float)

    def __init__(self, date, uniqueID, asset, value):
        self.date = date
        self.uniqueID = uniqueID
        self.asset = asset
        self.value = value

class OtherData(Base):
    __tablename__ = 'other_data'
    __table_args__ = {'schema': 'assetallocation'}

    id = Column(Integer, primary_key=True)
    uniqueID = Column(String)
    returns_col_name = Column(String)
    market_returns_col_name = Column(String)
    max_sharpe_weights = Column(String)
    max_sharpe_returns = Column(Float)
    max_sharpe_volatility = Column(Float)
    min_vol_weights = Column(String)
    min_vol_returns = Column(Float)
    min_vol_volatility = Column(Float)
    max_target_return = Column(Float)
    returns_range = Column(String)
    efficient_portfolios_weights = Column(String)
    efficient_portfolios_returns = Column(String)
    efficient_portfolios_volatilities = Column(String)
    max_drawdown = Column(String)
    betas = Column(String)
    holdings_metadata = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    freq = Column(String)
    risk_free_rate = Column(Float)
    num_portfolios = Column(Integer)
    missing_assets = Column(String)
    comments = Column(String)
    holdings_data = Column(String)

    def __init__(self, uniqueID, returns_col_name, market_returns_col_name, max_sharpe_weights, max_sharpe_returns, max_sharpe_volatility,
                 min_vol_weights, min_vol_returns, min_vol_volatility, max_target_return, returns_range,
                 efficient_portfolios_weights, efficient_portfolios_returns, efficient_portfolios_volatilities,
                 max_drawdown, betas, holdings_metadata, start_date, end_date, freq, risk_free_rate, num_portfolios, missing_assets, comments, holdings_data):
        self.uniqueID = uniqueID
        self.returns_col_name = returns_col_name
        self.market_returns_col_name = market_returns_col_name
        self.max_sharpe_weights = max_sharpe_weights
        self.max_sharpe_returns = max_sharpe_returns
        self.max_sharpe_volatility = max_sharpe_volatility
        self.min_vol_weights = min_vol_weights
        self.min_vol_returns = min_vol_returns
        self.min_vol_volatility = min_vol_volatility
        self.max_target_return = max_target_return
        self.returns_range = returns_range
        self.efficient_portfolios_weights = efficient_portfolios_weights
        self.efficient_portfolios_returns = efficient_portfolios_returns
        self.efficient_portfolios_volatilities = efficient_portfolios_volatilities
        self.max_drawdown = max_drawdown
        self.betas = betas
        self.holdings_metadata = holdings_metadata
        self.start_date = start_date
        self.end_date = end_date
        self.freq = freq
        self.risk_free_rate = risk_free_rate
        self.num_portfolios = num_portfolios
        self.missing_assets = missing_assets
        self.comments = comments
        self.holdings_data = holdings_data
