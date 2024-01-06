import numpy as np

class ZeroCashFlows():
    def __init__(self, seed=42):
        self.seed = seed
        self.cash_flow = None

    def fit(self, cash_flow=None):
        self.cash_flow = cash_flow

    def predict(self, horizon, n_paths=1):        
        # Generate new prices for each path
        cashflows = np.zeros(shape=(n_paths, horizon+1))
        
        return cashflows

