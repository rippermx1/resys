# Renko System
* The idea is to use Renko bars to create a system that can be used to trade any market.
* The system is based on the Renko bars and the Renko bars are based on the price action.
* The Mid Line Donchian Channer is used to validate the Entry and Trailing Stop.
* The Stochastic is used to validate the Entry and Exit Signals.

## Entry
* If the Stochastic %K and %D is below 5
    Means that we need to wait for the Stochastic %K to cross above the %D
        If this happens
            We need to to wait for Green Brick
                If the brick is Green 
                    We can place an Entry Order (Above the Mid Line Donchian Channel)
                    We can place an Stop Loss Order (Below the last Red Brick)


## Short
* If the Stochastic %K and %D is above 95
    Means that we need to wait for the Stochastic %K to cross below the %D
        If this happens
            We need to to wait for Red Brick
                If the brick is Red 
                    We can place an Entry Order (Below the Mid Line Donchian Channel)
                    We can place an Stop Loss Order (Above the last Green Brick)                    


# Management
* option 1: Buy Spot, Sell Spot
    * If conditions are meet for BUY:
        * Place a BUY order Above the Mid Line Donchian Channel
        * Place a STOP LOSS order Below the last Red Brick
        * Place a TAKE PROFIT order at 2:1 Risk Reward Ratio (If Sell Conditions are meet)
* optoin 2: Buy Future, Hedge Sell Future
    * If conditions are meet for BUY:
        * Place a BUY order Above the Mid Line Donchian Channel
        * Place a STOP LOSS order Below the last Red Brick
    * If Sell Conditions are meet:
        * Place a SELL order (Future) Below the Mid Line Donchian Channel
        * Place a STOP LOSS order Above the last Green Brick
        * This way we can hedge the previous BUY order
* option 3: Buy Spot, Sell Spot, Hedge Sell Future
    * If conditions are meet for BUY:
        * Place a BUY order Above the Mid Line Donchian Channel
        * Place a STOP LOSS order Below the last Red Brick
        * Place a TAKE PROFIT order when Sell Conditions are meet
    * If Sell Conditions are meet:
        * Place a SELL order (Future) Below the Mid Line Donchian Channel
        * Place a STOP LOSS order Above the last Green Brick
        * Place a TAKE PROFIT order when Buy Conditions are meet



# Notes:
* [ReSys Bot] Return Performance over time compared to the S&P 500 and Bitcoin

* [ReSys Bot] Buy Spot in Extreme Oversold Stochastic Area
* [ReSys Bot] Hedge Sell in Extreme Overbought Stochastic Area
* [Resys Bot] Open Long and Short to hedge Bitcoin movements

# Notes:

* To start ReSys use command: 
    - python main.py -symbol BTCUSDT -interval 5m -volume 10 -leverage 50 -brick_size 10 -trailing_ptc 0.25