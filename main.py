from src.returns import LogNormalReturns
from src.cashflows import NormalCashFlows, ZeroCashFlows
from src.optimization.om_discrete_cvar import create_model
from src.results import ResultsAnalyzer

from development.synth_data import generate_synth_prices, generate_synth_income, generate_synth_expenses
import src.constants as cte
import numpy as np
from pyomo.environ import SolverFactory
from pyomo.contrib import appsi
import time

import pandas as pd

price_data = generate_synth_prices()
returns_model = LogNormalReturns()
returns_model.fit(price_data)

income_data = generate_synth_income()
income_model = ZeroCashFlows()
income_model.fit(income_data)

expenses_data = generate_synth_expenses()
expenses_model = ZeroCashFlows()
expenses_model.fit(expenses_data)

non_cash_assets = list(price_data.columns)


prices_syms = returns_model.predict(horizon=cte.HORIZON_PERIODS, n_paths=cte.N_SCENARIOS, price_0=np.array([100,20]))
income_syms = income_model.predict(horizon=cte.HORIZON_PERIODS, n_paths=cte.N_SCENARIOS)
expenses_syms = expenses_model.predict(horizon=cte.HORIZON_PERIODS, n_paths=cte.N_SCENARIOS)
sScenarios = list(range(cte.N_SCENARIOS))
sInitialTime = [0]
sIntermediateTime = list(range(1, cte.HORIZON_PERIODS))
sFinalTime = [cte.HORIZON_PERIODS]
sNonInitialTimes = sIntermediateTime + sFinalTime
sNonFinalTimes = sInitialTime + sIntermediateTime
sTime = sInitialTime + sIntermediateTime + sFinalTime

data = {
    None: {
        'sInitialTime': {None: sInitialTime},
        'sIntermediateTime': {None: sIntermediateTime},
        'sFinalTime': {None: sFinalTime},
        'sNonCashAssets': {None: non_cash_assets},
        'sScenarios': {None: sScenarios},
        'pPrices': {(s_i,non_cash_assets[a_i], t_i): prices_syms[s_i,a_i,t_i] for s_i in sScenarios for t_i in sTime for a_i in range(len(non_cash_assets))},
        'pInitialNonCashAllocations': {a: 0 for a in non_cash_assets},
        'pInitialCashAllocations': {None: cte.STARTING_CASH},
        'pIncome': {(s_i,t_i): income_syms[s_i, t_i] for s_i in sScenarios for t_i in sNonFinalTimes},
        'pExpense': {(s_i,t_i): expenses_syms[s_i, t_i] for s_i in sScenarios for t_i in sNonFinalTimes},
        'pTradeFee': {None: cte.TRADING_FEE},
        'pCVaRAlpha': {None: cte.CVAR_ALPHA},
        'pCVaRGamma': {None: cte.CVAR_GAMMA},
    }
}

optimization_model = create_model()
instance = optimization_model.create_instance(data)
solver = SolverFactory('cbc')
# solver = SolverFactory('clp')
# solver = SolverFactory('glpk')
# solver = appsi.solvers.Cbc()
# solver = appsi.solvers.Cplex()
# solver = appsi.solvers.Highs()
# solver = appsi.solvers.Ipopt()

print(f'Starting to solve...')
t1 = time.time()
result_obj = solver.solve(instance, tee=True)
t2 = time.time()
print(f"Solved in {t2-t1:.2f} s")

analyzer = ResultsAnalyzer(instance)
analyzer.plot_ts(name='vTotalWealth', time_col='time',col_names=['scenario', 'time'], colors='scenario')
analyzer.plot_dist(name='vTotalWealth', col_names=['scenario', 'time'], filter={'time':5})
analyzer.plot_ci(name='vTotalWealth', time_col='time', scenario_col='scenario',filter=None, col_names=['scenario', 'time'], confidence=.95)
analyzer.plot_dist(name='pPrices', col_names=['scenario','asset','time'], filter={'time':5},colors='asset')
df = analyzer.get_df(name='vNonCashAllocations',col_names=['scenario', 'time'])
analyzer.plot_ci(name='vCashAllocations', time_col='time', scenario_col='scenario',filter=None, col_names=['scenario', 'time'], confidence=.95)
print(df)

pass