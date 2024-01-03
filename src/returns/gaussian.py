from scipy.stats import multivariate_normal
import numpy as np

class LogNormalReturns():
    def __init__(self, seed=42):
        self.seed = seed
        self.prices = None
        self.log_returns = None
        self.mean = None
        self.cov = None
        self.dist = None
        self.price_0 = None

    def fit(self, df_prices):
        self.prices = df_prices
        log_returns = np.log(df_prices / df_prices.shift(1)).dropna()
        self.mean = log_returns.mean().values
        self.cov = log_returns.cov().values
        self.dist = multivariate_normal(self.mean, self.cov)

    def set_price_0(self, price_0):
        self.price_0 = price_0

    def set_horizon(self, horizon):
        self.horizon = horizon

    def predict(self, horizon, n_paths=1, price_0=None):
        if self.mean is None or self.cov is None:
            raise ValueError("Model not fitted. Please use fit() method first.")
        
        if self.price_0 is None and price_0 is None:
            self.set_price_0(self.prices.iloc[-1,:].to_numpy())

        if price_0 is None:
            price_0 = self.price_0
        
        # Generate new prices for each path
        prices = np.zeros((n_paths, len(self.mean), horizon+1))
        prices[:, :, 0] = np.tile(price_0, (n_paths, 1))

        for t in range(1, horizon+1):
            log_returns_sampled = self.dist.rvs(size=n_paths, random_state=self.seed)
            prices[:, :, t] = prices[:, :, t] * np.exp(log_returns_sampled)


        return np.clip(prices, 0, None)

