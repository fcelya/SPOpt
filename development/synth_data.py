import numpy as np
import pandas as pd
import datetime

def generate_synth_prices():
    # Set a seed for reproducibility
    np.random.seed(42)

    # Number of days for which prices are generated
    num_days = 252

    # Mean log returns for the two assets
    mean_returns = [0.1, 0.15]

    # Covariance matrix
    cov_matrix = [[0.01, 0.01], [0.01, 0.04]]

    # Generate random log returns based on the normal distribution
    log_returns = np.random.multivariate_normal(mean_returns, cov_matrix, num_days)

    # Calculate prices based on the log returns
    prices = np.exp(np.cumsum(log_returns, axis=0))

    # Generate datetime index starting from a specific date
    start_date = datetime.datetime(2023, 1, 1)
    date_index = [start_date + datetime.timedelta(days=i) for i in range(num_days)]

    # Create a DataFrame with the generated prices
    df = pd.DataFrame(prices, columns=['Asset1', 'Asset2'], index=date_index)

    # Display the DataFrame
    return df

def generate_synth_income():
    return np.random.normal(20,2,size=200)

def generate_synth_expenses():
    return np.random.normal(16,4,size=200)
