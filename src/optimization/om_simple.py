import pyomo.environ as pe

def create_model():
    
    model = pe.AbstractModel()
    
    # Sets
    model.sTimes = pe.Set(within=pe.Integers)
    model.sAssets = pe.Set()
    model.sNonCashAssets = pe.Set(within=pe.sAssets)
    model.sScenarios = pe.Set(within=pe.Integers)
    
    # Parameters
    model.pReturns = pe.Param(model.sScenarios, model.sAssets, model.sTimes, mutable=True, within=pe.NonNegativeReals) # return as R=(1+r)
    model.pInitialAllocations = pe.Param(model.sAssets, mutable=True, within=pe.NonNegativeReals) # shorting not allowed
    model.pIncome = pe.Param(model.sScenarios, model.sTimes, mutable=True, within=pe.NonNegativeReals)
    model.pExpense = pe.Param(model.sScenarios, model.sTimes, mutable=True, within=pe.NonNegativeReals)
    
    # Scalar Parameters
    model.pTradeFee = pe.Param(mutable=True, within=pe.NonNegativeReals, default=0)
    
    # Variables
    model.vAllocations = pe.Var(model.sScenarios, model.sAssets, model.sTimes, mutable=True, domain=pe.NonNegativeReals, initialize=0) # shorting not allowed
    model.vTrades = pe.Var(model.sAssets, model.sTimes, mutable=True, domain=pe.Reals, initialize=0)
    model.vTradesAbs = pe.Var(model.sAssets, model.sTimes, mutable=True, domain=pe.NonNegativeReals, initialize=0)
    
    model.Objective = pe.Var(domain=pe.Reals, initialize=0)
    
    def c00_objective_function(model):
        pass # TODO
    
    # c01: Initial asset allocations
    def c01_initial_asset_allocations(model, s, a, t):
        if t == 0:
            return model.vAllocations[s,a,t] == model.pInitialAllocations[a]
        else:
            return pe.Constraint.Skip
    
    def c02_allocations_evolution_non_cash(model, s, a, t):
        if t == 0 or a == 0:
            return pe.Constraint.Skip
        else:
            return model.vAllocations[s,a,t] == (model.vAllocations[s,a,t-1] + model.vTrades[s,a,t-1]) * model.pReturns[s,a,t-1]
    
    def c03_0_absolute_value_trade_positive(model, a, t):
        return model.vTrades[a,t] <= model.vTradesAbs[a,t]
    
    def c03_1_absolute_value_trade_negative(model, a, t):
        return -model.vTrades[a,t] <= model.vTradesAbs[a,t]
    
    def c04_allocations_evolution_cash(model, s, a, t):
        if t == 0 or a != 0:
            return pe.Constraint.Skip
        else:
            return model.vAllocations[s,a,t] == (model.vAllocations[s,a,t-1] + model.vTrades[s,a,t-1]) * model.pReturns[s,a,t-1] + model.pIncome[s,t] - model.pExpense[s,t] - sum(model.vTradesAbs[ai,t] * model.pTradeFee[ai] for ai in model.NonCashAssets)
        
    # Objective function
    def obj_expression(model):
        return model.Objective
    
    # Activate constraints
    model.c02_dam_volume = pe.Constraint(model.sGates, model.sPresentFuture, rule=c02_dam_volume)
    
    # Objective function
    model.f_obj = pe.Objective(rule=obj_expression, sense=pe.maximize)
    
    return model