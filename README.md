# SPOpt: A flexible and hyperpersonalizable Stochastic Portfolio Optimization framework for individual investing

SPOpt is a framework aimed at solving the portfolio problem for individual investors in the most flexible but accurate way possible. It is based on stochastic linear programming and can be combined with many different modelling frameworks. Its basic implementation is based on PyOMO.

## Basic overview

The portfolio problem for the individual investor is, in a very simple sense, how to allocate his wealth accross different assets in order to maximize returns and minimize risk. 

In order to solve this problem, SPOpt combines three building blocks.

### Return Modelling

The first step to invest in different assets is to understand their return distribution. This modelling can be done through anything from a very simple but not very accurate Normal distribution to Hidden Markov Models to Bayesian Models to many other types of formulations. 

All modelling methods must have a `.fit()` and `.predict()` methods, used to infer parameters on historical data and to create the new predictions that will be used for the Asset Allocation step. 

All models are located in the `returns` module. Currently, the implemented return models are:

- `LogNormalReturns`: It models the asset logreturns as a multivariate normal distribution. It is fited with price data and outputs price simulations. 

### CashFlow Modelling

A fundamental aspect of the portfolio problem for the individual investor is the cashflows of the individual. That is, the expected income and expenses the investor will have. By incorporating these cashflows the proposed solution portfolio can be an integral solution for the individual, taking into account its exact needs and opportunities. 

All models are located in the `cashflows` module. Currently, the implemented cashflow models are:

- `ZeroCashFlows`: More of a helper function than a true model, it just provides a constant cashflow of 0. 

- `NormalCashFlows`: Models cashflows through a Normal distribution. This is the most simple model although not a very accurate one as it completely ignores seasonal information, trends, etc.

### Asset Allocation

In this final step the allocation accross different assets is determined. The allocation method is multiperiod stochastic linear programming formulation. It works by first simulating many different paths (potential future scenarios) with the previously specified models. Then the optimal decisions for all periods are chosen taking into account all these potential future scenarios. When using this in production, the first step is executed and in the next timestep the optimization is solved again with updated information, in a way similar to [Model Predictive Control](https://arxiv.org/abs/2103.10813). 

By using this formulation, many issues of traditional asset allocation methods can be overcome:
- Discrete investments: Only discrete amounts of shares can be bought, and when the individual's capital is not very large this greatly affects what assets can be bought and the real performance of the portfolio. 
- Trading fees: Through the multiperiod formulation trading fees are taken into account.
- Arbitrary constraints: Many constraints on asset types, diversification, cash amounts, etc. can be included.
- Personalizable objective function: By including the CVaR and Expectation a very comprehensive and realistic objective can be formulated. 

All models are located in the `optimization` module. Currently, the implemented optimization models are:

- `om_discrete`: In this model there are multiple assets for which the price evolution in each scenario is provided. Trading decisions as shares bought/sold are optimized for each period. Trading fees are included percentagewise on each buy/sell trade. Cash must be non negative for all scenarios. The objective funciton is the expected final wealth. This model does not allow margin or short investing, nor does it include a return for cash. 
- `om_discrete_cvar`: Equal to the previous model, but the objective function is a linear combination between the expected total final wealth and the CVaR on the total final wealth.
- `om_discrete_cvar_negativecash`: Equal to the previous model, but it allows a certain percentage of scenarios to have cash below a certain threshold, including negative cash.


Any and all proposals and contributions are welcome!