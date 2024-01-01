import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from prophet import Prophet

#data = pd.read_csv("AAPL.csv") 

def prophet_model(data: pd.DataFrame, daily_seasonality: bool = True):
    '''Create a Prophet model
    Input must be a dataframe with the columns "Date" and "Close".

    Args:
        data (pd.DataFrame): The data used to train the model
        daily_seasonality (bool): Whether to include daily seasonality in the model

    Returns:
        Prophet: The model'''
    # Select only the important features i.e. the date and price
    data = data[["Date","Close"]] # select Date and Price# Rename the features: These names are NEEDED for the model fitting
    data = data.rename(columns = {"Date":"ds","Close":"y"}) #renaming the columns of the dataset
    described_data = data.describe()
    
    model = Prophet(daily_seasonality = daily_seasonality) # the Prophet class (model)
    return model.fit(data) # fit the model using all data

def prophet_forecast(model: Prophet, days: int = 365):
    '''Predict the future price of the stock using the Prophet

    Args:
        model (Prophet): The model
        days (int): The number of days in the future to predict

    Returns:
        pd.DataFrame: The prediction of the model'''
    future = model.make_future_dataframe(periods=days) #we need to specify the number of days in future
    prediction = model.predict(future)
    return prediction

def plot_prophet_model_matplot(model, prediction):
    '''Plot the prediction of the model using matplot
    
    Args:
        model (Prophet): The model
        prediction (pd.DataFrame): The prediction of the model
        
    Returns:
        plt: The matplot figure'''
    model.plot(prediction)
    plt.title("Prediction of the Apple Stock Price using the Prophet")
    plt.xlabel("Date")
    plt.ylabel("Close Stock Price")
    #plt.show()
    return plt

def plot_prophet_model_components_matplot(model, prediction):
    '''Plot the components of the model using matplot
    Components: trend, weekly seasonality, yearly seasonality, daily seasonality
    
    Args:
        model (Prophet): The model
        prediction (pd.DataFrame): The prediction of the model
        
    Returns:
        plt: The matplot figure
        '''
    model.plot_components(prediction)
    #plt.show()
    return plt

def plot_prophet_model_plotly(prediction, data,) -> go.Figure:
    '''Plot the prediction of the model using plotly
    
    Args:
        prediction (pd.DataFrame): The prediction of the model
        data (pd.DataFrame): The data used to train the model
    
    Returns:
        go.Figure: The plotly figure
        
    Example:
        >>> data = pd.read_csv("AAPL.csv")
        >>> model = prophet_model(data)
        >>> prediction = prophet_forecast(model)
        >>> plot_prophet_model_plotly(prediction, data)
        '''
    prediction_from_end_of_actual_data = prediction.tail(365)

    # Plot the actual data
    trace_actual = go.Scatter(x=data['ds'], y=data['y'], mode='lines', name='Actual', line=dict(color='blue'))

    # Plot the prediction data
    trace_prediction = go.Scatter(x=prediction['ds'], y=prediction['yhat'], mode='lines', name='Prediction', line=dict(color='red'))

    # Plot the uncertainty interval
    trace_upper = go.Scatter(
        x=prediction['ds'],
        y=prediction['yhat_upper'],
        fill=None,
        mode='lines',
        line=dict(color='rgba(255, 0, 0, 0.3)'),
        name='Upper Bound'
    )

    trace_lower = go.Scatter(
        x=prediction['ds'],
        y=prediction['yhat_lower'],
        fill='tonexty',
        mode='lines',
        line=dict(color='rgba(255, 0, 0, 0.3)'),
        name='Lower Bound'
    )

    # Create the figure and add the traces
    fig = go.Figure(data=[trace_actual, trace_prediction, trace_upper, trace_lower])

    # Update layout with titles and axis labels
    fig.update_layout(
        title="Prediction of the Google Stock Price using Prophet",
        xaxis_title="Date",
        yaxis_title="Close Stock Price"
    )

    # Show the plot
    return fig


#===================================================================================================
# ARIMA MODELS
#===================================================================================================

from pmdarima import auto_arima
#from sklearn.metrics import mean_squared_error, mean_absolute_error


# Function to load and preprocess asset data
def load_asset_data(asset_file):
    asset_name = asset_file.replace('.csv', '')
    df = pd.read_csv(asset_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df.set_index('Date', inplace=True)
    return df['Close'], asset_name

def apply_weights(df, weights):
    # Assumes that df.columns and weights.keys() are aligned
    return df * np.array(list(weights.values()))

def arima_model_multi_assets(data: pd.DataFrame, asset_weights: dict):
    '''Create an ARIMA model
    Input must be a dataframe with different assets close prices

    Args:
        data (pd.DataFrame): The data used to train the model 
        asset_weights (dict): The weights of the assets i.e. {"TSLA": 0.4, "AAPL": 0.3, "GOOGL": 0.3}
    
    Returns:
        dict: Contains actual_prices_mean, portfolio_predictions_mean, conf_int_lower, conf_int_upper'''

    assert np.isclose(sum(asset_weights.values()), 1), "Weights should sum up to 1"

    data = data.copy()  # Work on a copy of the data
    data.fillna(method='ffill', inplace=True)
    data.replace([np.inf, -np.inf], np.nan, inplace=True)
    data.dropna(inplace=True)

    portfolio_predictions = pd.DataFrame()
    portfolio_std_errors = pd.DataFrame()
    actual_prices = pd.DataFrame()

    n_steps = 30

    for asset_name in asset_weights.keys():  # Use asset_weights instead of data.columns to ensure they align

        if asset_name not in data.columns:
            raise ValueError(f"Asset {asset_name} not found in data")

        close_prices = data[asset_name]
        train_data, test_data = close_prices[0:int(len(close_prices)*0.7)], close_prices[int(len(close_prices)*0.7):]
        training_data = train_data.values

        model = auto_arima(training_data, trace=True, error_action='ignore', suppress_warnings=True)
        model_fit = model.fit(training_data)

        model_predictions, conf_int = model_fit.predict(n_periods=n_steps, return_conf_int=True)
        std_errors = (conf_int[:, 1] - conf_int[:, 0])/2

        next_day = train_data.index[-1] + pd.DateOffset(days=1)
        prediction_dates = pd.date_range(start=next_day, periods=n_steps)

        portfolio_predictions[asset_name] = pd.Series(model_predictions, index=prediction_dates)
        portfolio_std_errors[asset_name] = pd.Series(std_errors, index=prediction_dates)
        actual_prices[asset_name] = close_prices

    portfolio_predictions = apply_weights(portfolio_predictions, asset_weights)
    portfolio_std_errors = apply_weights(portfolio_std_errors, asset_weights)
    actual_prices = apply_weights(actual_prices, asset_weights)

    portfolio_predictions_mean = portfolio_predictions.sum(axis=1)

    portfolio_std = np.sqrt(np.dot(list(asset_weights.values()), np.dot(portfolio_std_errors.cov(), list(asset_weights.values()))))

    conf_int_lower = portfolio_predictions_mean - 1.96 * portfolio_std
    conf_int_upper = portfolio_predictions_mean + 1.96 * portfolio_std

    actual_prices_mean = actual_prices.sum(axis=1)

    obj = {
        "actual_prices_mean": actual_prices_mean,
        "portfolio_predictions_mean": portfolio_predictions_mean,
        "conf_int_lower": conf_int_lower,
        "conf_int_upper": conf_int_upper
    }

    return obj


def plot_arima_model_plotly(obj):
    '''Plot the prediction of the model using plotly
    
    Args:
        obj (dict): The object containing the data
        
    Returns:
        go.Figure: The plotly figure'''

    # Create figure
    fig = go.Figure()

    # Add traces
    fig.add_trace(
        go.Scatter(x=obj['actual_prices_mean'].index, y=obj['actual_prices_mean'], mode='lines', name='Actual Portfolio Value')
    )

    fig.add_trace(
        go.Scatter(x=obj['portfolio_predictions_mean'].index, y=obj['portfolio_predictions_mean'], mode='lines', name='Predicted Portfolio Value')
    )

    fig.add_trace(
        go.Scatter(x=obj['portfolio_predictions_mean'].index, y=obj['conf_int_lower'], fill=None, mode='lines', name='Lower Confidence Interval', line_color='pink')
    )

    fig.add_trace(
        go.Scatter(x=obj['portfolio_predictions_mean'].index, y=obj['conf_int_upper'], fill='tonexty', mode='lines', name='Upper Confidence Interval', line_color='pink')
    )

    # Edit the layout
    fig.update_layout(title='Portfolio Value Over Time', xaxis_title='Time', yaxis_title='Value')

    return fig

