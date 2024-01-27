import pandas as pd
from development.synth_data import generate_synth_income, generate_synth_expenses
from src.returns import LogNormalReturns
from src.cashflows import NormalCashFlows
from src.results import ResultsAnalyzer
from src.optimization.om_continuous_cvar import create_model as create_model_continuous
from pyomo.environ import SolverFactory
from pyomo.opt.results import SolverStatus
import time

df_prices = pd.read_csv('./data/monthly_example_3.csv', index_col=0, parse_dates=True)
print('Read prices')
arr_income = generate_synth_income(mean=2000, std=50)
arr_expenses = generate_synth_expenses(mean=1600, std=80)
print('Read income and expenses')
returns_model = LogNormalReturns()
returns_model.fit(df_prices=df_prices)
print('Fitted returns')
income_model = NormalCashFlows()
income_model.fit(cash_flow=arr_income)
expenses_model = NormalCashFlows()
expenses_model.fit(cash_flow=arr_expenses)
print('Fitted cashflows')
N_SCENARIOS = 300 # The more scenarios the more accurate the solution but more difficult to solve
HORIZON_PERIODS = 5*12 # In this case, number of weeks to plan for. Note that only the first step is executed, but plannig several steps ahead provides more accurate and realistic deicisions
STARTING_CASH = 100_000
TRADING_FEE = 0.01
CVAR_ALPHA1 = 0.5 # The quantile for which the CVaR is calculated. The smaller the more the extreme cases will be taken into account. 
CVAR_GAMMA1 = 0.8 # Weight given to CVaR in the objective function 

prices_syms = returns_model.predict(horizon=HORIZON_PERIODS, n_paths=N_SCENARIOS) # Prices are simulated
income_syms = income_model.predict(horizon=HORIZON_PERIODS, n_paths=N_SCENARIOS) # Income is simulated
expenses_syms = expenses_model.predict(horizon=HORIZON_PERIODS, n_paths=N_SCENARIOS) # Expenses are simulated
print('Generated simulated paths')
non_cash_assets = list(df_prices.columns)
sScenarios = list(range(N_SCENARIOS))
sInitialTime = [0]
sIntermediateTime = list(range(1, HORIZON_PERIODS))
sFinalTime = [HORIZON_PERIODS]
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
        'pInitialCashAllocations': {None: STARTING_CASH},
        'pIncome': {(s_i,t_i): income_syms[s_i, t_i] for s_i in sScenarios for t_i in sNonFinalTimes},
        'pExpense': {(s_i,t_i): expenses_syms[s_i, t_i] for s_i in sScenarios for t_i in sNonFinalTimes},
        'pTradeFee': {None: TRADING_FEE},
        'pCVaRAlpha': {None: CVAR_ALPHA1},
        'pCVaRGamma': {None: CVAR_GAMMA1},
    }
}

optimization_model = create_model_continuous()
instance = optimization_model.create_instance(data)
solver = SolverFactory('gurobi', solver_io="python")
solver.options['TimeLimit'] = 300
solver.options['NoRelHeurTime'] = 120

print(f'Starting to solve...')
t1 = time.time()
result_obj = solver.solve(instance, tee=True)
if result_obj.Solver.Status != SolverStatus.ok:
    result_obj.Solver.Status = SolverStatus.warning
    instance.solutions.load_from(result_obj)   
t2 = time.time()
print(f"Solved in {t2-t1:.2f} s")
print(result_obj['Problem'])
print(result_obj['Solver'])


analyzer = ResultsAnalyzer(instance)
analyzer.plot_ci(name='vTotalWealth', time_col='time', scenario_col='scenario',filter=None, col_names=['scenario', 'time'], confidence=.90, inline_plot=False)
analyzer.plot_ci(name='vCashAllocations', time_col='time', scenario_col='scenario',filter=None, col_names=['scenario', 'time'], confidence=.95, inline_plot=False)
analyzer.plot_ts(name='vNonCashAllocations', time_col='time', col_names=['assets', 'time'], colors='assets')
# analyzer.save_csv(name='vNonCashAllocations', csv_path_name='assets_ts.csv', col_names=['assets', 'time'])