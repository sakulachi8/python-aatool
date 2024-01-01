########################
# Create Graphs
########################

def plot_efficient_frontier(mean_returns, cov_matrix, num_portfolios, risk_free_rate):
    results, _ = monte_carlo_simulation(num_portfolios, mean_returns, cov_matrix, risk_free_rate)
    plt.figure(figsize=(10, 7))
    plt.scatter(results[0, :], results[1, :], c=results[2, :], cmap='YlGnBu', marker='o', s=10, alpha=0.3)
    plt.colorbar()
    plt.scatter(results[0, :].min(), results[1, :].max(), marker='*', color='r', s=500)
    plt.scatter(results[0, :].max(), results[1, :].min(), marker='*', color='r', s=500)
    plt.title('Efficient Frontier')
    plt.xlabel('Volatility (Std. Deviation)')
    plt.ylabel('Returns')
    plt.show()

def plot_portfolio_weights(weights_record):
    weights_df = pd.DataFrame(weights_record)
    plt.figure(figsize=(10, 7))
    for c in weights_df.columns.values:
        plt.plot(weights_df.index, weights_df[c], lw=1, label=c)
    plt.legend(loc='upper right', fontsize=10)
    plt.xlabel('Simulation')
    plt.ylabel('Weights')
    plt.title('Portfolio Weights')
    plt.show()

def plot_portfolio_diversification(weights_record):
    weights_df = pd.DataFrame(weights_record)
    div_index = weights_df.apply(diversification_index, axis=1)
    plt.figure(figsize=(10, 7))
    plt.plot(div_index.index, div_index, lw=1)
    plt.xlabel('Simulation')
    plt.ylabel('Diversification Index')
    plt.title('Portfolio Diversification')
    plt.show()

def plot_portfolio_performance(weights_record, mean_returns, cov_matrix, risk_free_rate):
    results = np.zeros((4, len(weights_record)))
    for i in range(len(weights_record)):
        portfolio_std_dev, portfolio_return = portfolio_annualized_performance(weights_record[i], mean_returns, cov_matrix)
        results[0, i] = portfolio_std_dev
        results[1, i] = portfolio_return
        results[2, i] = (portfolio_return - risk_free_rate) / portfolio_std_dev
        results[3, i] = diversification_index(weights_record[i])
    plt.figure(figsize=(10, 7))
    plt.scatter(results[0, :], results[1, :], c=results[2, :], cmap='YlGnBu', marker='o', s=10, alpha=0.3)
    plt.colorbar()
    plt.scatter(results[0, :].min(), results[1, :].max(), marker='*', color='r', s=500)
    plt.scatter(results[0, :].max(), results[1, :].min(), marker='*', color='r', s=500)
    plt.title('Portfolio Performance')
    plt.xlabel('Volatility (Std. Deviation)')
    plt.ylabel('Returns')
    plt.show()

def plot_portfolio_skewness_kurtosis(weights_record, returns_data):
    results = np.zeros((2, len(weights_record)))
    for i in range(len(weights_record)):
        results[0, i], results[1, i] = portfolio_skewness_kurtosis(weights_record[i], returns_data)
    plt.figure(figsize=(10, 7))
    plt.scatter(results[0, :], results[1, :], marker='o', s=10, alpha=0.3)
    plt.scatter(results[0, :].min(), results[1, :].max(), marker='*', color='r', s=500)
    plt.scatter(results[0, :].max(), results[1, :].min(), marker='*', color='r', s=500)
    plt.title('Portfolio Skewness vs. Kurtosis')
    plt.xlabel('Skewness')
    plt.ylabel('Kurtosis')
    plt.show()

def plot_portfolio_drawdown(weights_record, price_data):
    results = np.zeros((1, len(weights_record)))
    for i in range(len(weights_record)):
        results[0, i] = max_drawdown(price_data, weights_record[i])
    plt.figure(figsize=(10, 7))
    plt.scatter(range(len(weights_record)), results[0, :], marker='o', s=10, alpha=0.3)
    plt.scatter(results[0, :].min(), results[0, :].max(), marker='*', color='r', s=500)
    plt.title('Portfolio Drawdown')
    plt.xlabel('Simulation')
    plt.ylabel('Max Drawdown')
    plt.show()



def plot_portfolio_sharpe_ratio(weights_record, mean_returns, cov_matrix, risk_free_rate):
    results = np.zeros((1, len(weights_record)))
    for i in range(len(weights_record)):
        results[0, i] = sharpe_ratio(weights_record[i], mean_returns, cov_matrix, risk_free_rate)
    plt.figure(figsize=(10, 7))
    plt.scatter(range(len(weights_record)), results[0, :], marker='o', s=10, alpha=0.3)
    plt.scatter(results[0, :].min(), results[0, :].max(), marker='*', color='r', s=500)
    plt.title('Portfolio Sharpe Ratio')
    plt.xlabel('Simulation')
    plt.ylabel('Sharpe Ratio')
    plt.show()

def plot_portfolio_sortino_ratio(weights_record, mean_returns, cov_matrix, risk_free_rate):
    results = np.zeros((1, len(weights_record)))
    for i in range(len(weights_record)):
        results[0, i] = sortino_ratio(weights_record[i], mean_returns, cov_matrix, risk_free_rate)
    plt.figure(figsize=(10, 7))
    plt.scatter(range(len(weights_record)), results[0, :], marker='o', s=10, alpha=0.3)
    plt.scatter(results[0, :].min(), results[0, :].max(), marker='*', color='r', s=500)
    plt.title('Portfolio Sortino Ratio')
    plt.xlabel('Simulation')
    plt.ylabel('Sortino Ratio')
    plt.show()

def plot_portfolio_treynor_ratio(weights_record, mean_returns, cov_matrix, risk_free_rate, market_return):
    results = np.zeros((1, len(weights_record)))
    for i in range(len(weights_record)):
        results[0, i] = treynor_ratio(weights_record[i], mean_returns, cov_matrix, risk_free_rate, market_return)
    plt.figure(figsize=(10, 7))
    plt.scatter(range(len(weights_record)), results[0, :], marker='o', s=10, alpha=0.3)
    plt.scatter(results[0, :].min(), results[0, :].max(), marker='*', color='r', s=500)
    plt.title('Portfolio Treynor Ratio')
    plt.xlabel('Simulation')
    plt.ylabel('Treynor Ratio')
    plt.show()

def plot_portfolio_jensens_alpha(weights_record, mean_returns, cov_matrix, risk_free_rate, market_return):
    results = np.zeros((1, len(weights_record)))
    for i in range(len(weights_record)):
        results[0, i] = jensens_alpha(weights_record[i], mean_returns, cov_matrix, risk_free_rate, market_return)
    plt.figure(figsize=(10, 7))
    plt.scatter(range(len(weights_record)), results[0, :], marker='o', s=10, alpha=0.3)
    plt.scatter(results[0, :].min(), results[0, :].max(), marker='*', color='r', s=500)
    plt.title('Portfolio Jensen\'s Alpha')
    plt.xlabel('Simulation')
    plt.ylabel('Jensen\'s Alpha')
    plt.show()