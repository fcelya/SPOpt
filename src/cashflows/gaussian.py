from scipy.stats import norm
import numpy as np

class NormalCashFlows():
    def __init__(self, seed=42):
        self.seed = seed
        self.cash_flow = None
        self.mean = None
        self.var = None
        self.dist = None

    def fit(self, cash_flow):
        self.cash_flow = cash_flow
        self.mean = np.mean(cash_flow)
        self.var = np.var(cash_flow)
        self.dist = norm(self.mean, self.var)

    def predict(self, horizon, n_paths=1):
        if self.mean is None or self.var is None:
            raise ValueError("Model not fitted. Please use fit() method first.")
        
        # Generate new prices for each path
        cashflows = np.clip(self.dist.rvs(size=(n_paths, horizon),random_state=self.seed), 0, None)
        
        return cashflows

