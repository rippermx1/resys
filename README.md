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