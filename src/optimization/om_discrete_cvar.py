import pyomo.environ as pe

def create_model():
    
    model = pe.AbstractModel()
    
    # Sets
    model.sInitialTime = pe.Set(within=pe.NonNegativeIntegers, initialize=[0])
    model.sIntermediateTime = pe.Set(within=pe.NonNegativeIntegers)
    model.sFinalTime = pe.Set(within=pe.NonNegativeIntegers)
    model.sTime = model.sInitialTime | model.sIntermediateTime | model.sFinalTime
    model.sNonInitialTime = model.sIntermediateTime | model.sFinalTime
    model.sNonFinalTime = model.sInitialTime | model.sIntermediateTime
    model.sNonCashAssets = pe.Set()
    model.sScenarios = pe.Set(within=pe.Integers)
    
    # Parameters
    model.pPrices = pe.Param(model.sScenarios, model.sNonCashAssets, model.sTime, mutable=True, within=pe.NonNegativeReals)
    model.pInitialNonCashAllocations = pe.Param(model.sNonCashAssets, mutable=True, within=pe.NonNegativeIntegers) # shorting not allowed
    model.pInitialCashAllocations = pe.Param(mutable=True, within=pe.NonNegativeReals)
    model.pIncome = pe.Param(model.sScenarios, model.sNonFinalTime, mutable=True, within=pe.NonNegativeReals)
    model.pExpense = pe.Param(model.sScenarios, model.sNonFinalTime, mutable=True, within=pe.NonNegativeReals)
    model.pTradeFee = pe.Param(mutable=True, within=pe.NonNegativeReals, default=0)
    model.pCVaRAlpha = pe.Param(mutable=True, within=pe.NonNegativeReals, default=0.05)
    model.pCVaRGamma = pe.Param(mutable=True, within=pe.NonNegativeReals, default=0.0)
    # Variables
    model.vCashAllocations = pe.Var(model.sScenarios, model.sTime, domain=pe.NonNegativeReals, initialize=0) # shorting not allowed
    model.vNonCashAllocations = pe.Var(model.sNonCashAssets, model.sTime, domain=pe.NonNegativeIntegers, initialize=0) # shorting not allowed
    model.vCashTrades = pe.Var(model.sScenarios, model.sNonFinalTime, domain=pe.Reals, initialize=0)
    model.vCashTradesAbs = pe.Var(model.sScenarios, model.sNonFinalTime, domain=pe.NonNegativeReals, initialize=0)
    model.vNonCashTrades = pe.Var(model.sNonCashAssets, model.sNonFinalTime, domain=pe.Integers, initialize=0)
    model.vNonCashTradesAbs = pe.Var(model.sNonCashAssets, model.sNonFinalTime, domain=pe.NonNegativeIntegers, initialize=0)
    
    model.vCVaR = pe.Var(model.sFinalTime, domain=pe.Reals, initialize=0)
    model.vVaR = pe.Var(model.sFinalTime, domain=pe.Reals, initialize=0)
    model.vLoss = pe.Var(model.sScenarios, model.sFinalTime, domain=pe.NonNegativeReals, initialize=0)

    model.vTotalWealth = pe.Var(model.sScenarios, model.sTime, domain=pe.NonNegativeReals)

    model.Objective = pe.Var(domain=pe.Reals, initialize=0)
    
    def c00_objective_function(model, t):
        n_scenarios = len(model.sScenarios)
        return model.Objective == sum(model.vTotalWealth[s,t] for s in model.sScenarios)/n_scenarios*(1-model.pCVaRGamma) - model.vCVaR[t]*model.pCVaRGamma
        
    def c01_initial_non_cash_allocations(model, a, t):
        return model.vNonCashAllocations[a,t] == model.pInitialNonCashAllocations[a]

    def c02_initial_cash_allocations(model, s, t):
        return model.vCashAllocations[s,t] == model.pInitialCashAllocations
        
    def c03_allocations_evolution_non_cash(model, a, t):
        return model.vNonCashAllocations[a,t] == model.vNonCashAllocations[a,t-1] + model.vNonCashTrades[a,t-1]
    
    def c04_allocations_evolution_cash(model, s, t):
        return model.vCashAllocations[s,t] == model.vCashAllocations[s,t-1] + model.vCashTrades[s,t-1] + model.pIncome[s,t-1] - model.pExpense[s,t-1]
    
    def c05_absolute_value_cash_trade_positive(model, s, t):
        return model.vCashTrades[s,t] <= model.vCashTradesAbs[s,t]
    
    def c06_absolute_value_cash_trade_negative(model, s, t):
        return -model.vCashTrades[s,t] <= model.vCashTradesAbs[s,t]
    
    def c07_absolute_value_non_cash_trade_positive(model, a, t):
        return model.vNonCashTrades[a,t] <= model.vNonCashTradesAbs[a,t]
    
    def c08_absolute_value_non_cash_trade_negative(model, a, t):
        return -model.vNonCashTrades[a,t] <= model.vNonCashTradesAbs[a,t]
        
    def c09_self_financing(model, s, t):
        return sum(model.vNonCashTrades[a,t]*model.pPrices[s,a,t] for a in model.sNonCashAssets) + model.vCashTrades[s,t] + sum(model.vNonCashTradesAbs[a,t]*model.pPrices[s,a,t]*model.pTradeFee for a in model.sNonCashAssets) + model.vCashTradesAbs[s,t]*model.pTradeFee <= 0
        
    def c10_total_wealth(model, s, t):
        return model.vTotalWealth[s,t] == model.vCashAllocations[s,t] + sum(model.vNonCashAllocations[a,t]*model.pPrices[s,a,t] for a in model.sNonCashAssets)
     
    def c11_final_wealth_cvar_loss(model, s, t):
        return model.vLoss[s,t] >= - model.vVaR[t] - model.vTotalWealth[s,t]

    def c12_cvar(model, t):
        n_scenarios = len(model.sScenarios)
        return model.vCVaR[t] == model.vVaR[t] + 1/model.pCVaRAlpha/n_scenarios*sum(model.vLoss[s,t] for s in model.sScenarios)
        

    # Objective function
    def obj_expression(model):
        return model.Objective
    
    # Activate constraints
    model.c00_objective_function = pe.Constraint(model.sFinalTime, rule=c00_objective_function)
    model.c01_initial_non_cash_allocations = pe.Constraint(model.sNonCashAssets, model.sInitialTime, rule=c01_initial_non_cash_allocations)
    model.c02_initial_cash_allocations = pe.Constraint(model.sScenarios, model.sInitialTime, rule=c02_initial_cash_allocations)
    model.c03_allocations_evolution_non_cash = pe.Constraint(model.sNonCashAssets, model.sNonInitialTime, rule=c03_allocations_evolution_non_cash)
    model.c04_allocations_evolution_cash = pe.Constraint(model.sScenarios, model.sNonInitialTime, rule=c04_allocations_evolution_cash)
    model.c05_absolute_value_cash_trade_positive = pe.Constraint(model.sScenarios, model.sNonFinalTime, rule=c05_absolute_value_cash_trade_positive)
    model.c06_absolute_value_cash_trade_negative = pe.Constraint(model.sScenarios, model.sNonFinalTime, rule=c06_absolute_value_cash_trade_negative)
    model.c07_absolute_value_non_cash_trade_positive = pe.Constraint(model.sNonCashAssets, model.sNonFinalTime, rule=c07_absolute_value_non_cash_trade_positive)
    model.c08_absolute_value_non_cash_trade_negative = pe.Constraint(model.sNonCashAssets, model.sNonFinalTime, rule=c08_absolute_value_non_cash_trade_negative)
    model.c09_self_financing = pe.Constraint(model.sScenarios, model.sNonFinalTime, rule=c09_self_financing)
    model.c10_total_wealth = pe.Constraint(model.sScenarios, model.sTime, rule=c10_total_wealth)
    model.c11_final_wealth_cvar_loss = pe.Constraint(model.sScenarios, model.sFinalTime, rule=c11_final_wealth_cvar_loss)
    model.c12_cvar = pe.Constraint(model.sFinalTime, rule=c12_cvar)


    # Objective function
    model.f_obj = pe.Objective(rule=obj_expression, sense=pe.maximize)
    
    return model