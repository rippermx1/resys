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


# Types of Bot
* Renko System
    * Renko System
    * Renko System - Buy Spot, Sell Spot
    * Renko System - Buy Future, Hedge Sell Future
    * Renko System - Buy Spot, Sell Spot, Hedge Sell Future
# NOTES
* Get a look back (default for 5 minutes) of last 12 hours (720 minutes) of Renko Bars since current time
* Get Maximas and Minimas of the last 12 hours of Renko Bars
* Get the Avg of the Maximas and Minimas 
    - Maximas = sum(Hihgs) / count(Hihgs)
    - Minimas = sum(Lows) / count(Lows)
    - Calculate Maximas Zone [Level 0] = Maximas[0] - factor
    - Calculate Maximas Zone [Level 1] = Maximas[0] + factor
    - Calculate Minimas Zone [Level 0] = Minimas[0] - factor
    - Calculate Minimas Zone [Level 1] = Minimas[0] + factor
* Get data from 1m timeframe 
* Get renko bars from 1m data
* Find sell signals 
    - if current close is below (Minimas[1] - factor) and above (Minimas[0] - factor) and RESYS CONDITIONS
* Find buy signals
    - if current close is below (Minimas[1] - factor) and above (Minimas[0] - factor) and RESYS CONDITIONS



# Notes:
* [ReSys Bot] Return Performance over time compared to the S&P 500 and Bitcoin

* [ReSys Bot] Buy Spot in Extreme Oversold Stochastic Area
* [ReSys Bot] Hedge Sell in Extreme Overbought Stochastic Area
* [Resys Bot] Open Long and Short to hedge Bitcoin movements

# Notes:

* To start ReSys (If DONT HAVE any Bot Created) use command: 
    - python main.py -symbol BTCUSDT -interval 5m -volume 10 -leverage 50 -brick_size 10 -trailing_ptc 0.25 

* To start ReSys (If you HAVE at least 1 Bot Created) use command: 
    - python main.py -secret [secret] -bot_id [bot_id]
    
# API
* [NOTE] In order to use Good Packages you need to export python path project
* export PYTHONPATH="${PYTHONPATH}:/path/to/your/project/"
# For Windows
* set PYTHONPATH=%PYTHONPATH%;C:\path\to\your\project\


# Stochastic System
* Sell if price is above K% (95 upper)
* Buy if price is below K% (5 lower)
- "Works Fine if price movements are fast and strong (High Volatility)"
# Grid System

# OS
* os.kill(os.getppid(), signal.SIGTERM)
* sys.argv[1]
* p = subprocess.Popen("start cmd /k python D:\CVA_Capital\Bots\script_1.py {} {} {} {} {}".format(symbol, entry_price, entry_order_id, stop_order_id, qty), shell=True)

# subprocess.call('python D:\CVA_Capital\Bots\script_1.py BTCUSDT', creationflags=subprocess.CREATE_NEW_CONSOLE)
# subprocess.call('python D:\CVA_Capital\Bots\script_2.py ETHUSDT', creationflags=subprocess.CREATE_NEW_CONSOLE)
# subprocess.Popen("start cmd /k python D:\CVA_Capital\Bots\script_2.py", shell=True) 


# NOTES
* Mientras el precio se desplaza X cantidad de USD el RSI 

# Strategies
* Scalping
    - Donchian Slow (Mid as Trailing Stop)
    - Donchian Fast as Signal
    - Stochastic as Signal
    - R/R 1:1.5
    - 1m
