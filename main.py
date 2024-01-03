from src.returns import LogNormalReturns
from src.cashflows import NormalCashFlows
from src.optimization.om_discrete import create_model
from development.synth_data import generate_synth_prices, generate_synth_income, generate_synth_expenses
import src.constants as cte
import numpy as np
from pyomo.environ import SolverFactory

price_data = generate_synth_prices()
returns_model = LogNormalReturns()
returns_model.fit(price_data)

income_data = generate_synth_income()
income_model = NormalCashFlows()
income_model.fit(income_data)

expenses_data = generate_synth_expenses()
expenses_model = NormalCashFlows()
expenses_model.fit(expenses_data)

cash_assets = ['cash']
non_cash_assets = list(price_data.columns)
assets = cash_assets + non_cash_assets


pInitialAllocations = [cte.STARTING_CASH] + [0]*len(non_cash_assets)
prices_syms = returns_model.predict(horizon=cte.HORIZON_PERIODS, n_paths=cte.N_SCENARIOS, price_0=np.array([100,20]))
income_syms = income_model.predict(horizon=cte.HORIZON_PERIODS, n_paths=cte.N_SCENARIOS)
expenses_syms = income_model.predict(horizon=cte.HORIZON_PERIODS, n_paths=cte.N_SCENARIOS)
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
        'sCashAssets': {None: cash_assets},
        'sScenarios': {None: sScenarios},
        'pPrices': {(s_i,non_cash_assets[a_i], t_i): prices_syms[s_i,a_i,t_i] for s_i in sScenarios for t_i in sTime for a_i in range(len(non_cash_assets))},
        'pInitialAllocations': {assets[i]: pInitialAllocations[i] for i in range(len(assets))},
        'pIncome': {(s_i,t_i): income_syms[s_i, t_i-1] for s_i in sScenarios for t_i in sNonFinalTimes},
        'pExpense': {(s_i,t_i): expenses_syms[s_i, t_i-1] for s_i in sScenarios for t_i in sNonFinalTimes},
        'pNScenarios': {None: cte.N_SCENARIOS},
        'pTradeFee': {None: cte.TRADING_FEE},
    }
}

optimization_model = create_model()
instance = optimization_model.create_instance(data)
instance.pprint()
opt = SolverFactory('glpk')
result_obj = opt.solve(instance, tee=True)
pass