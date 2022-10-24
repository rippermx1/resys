from backtest import get_signals
from dotenv import load_dotenv
import os
from pandas import DataFrame
from binance import Client
from renko import Renko
import pandas_ta as ta
load_dotenv()

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
STOCH_OVERBOUGHT = 95
STOCH_OVERSOLD   = 5
UP   = 'up'
DOWN = 'down'
BRICK_SIZE_10 = 10


def get_data():
    data = client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_5MINUTE, limit=1000)
    data = DataFrame(data)
    data = data.iloc[:,[0,1,2,3,4,5]]
    data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    data[['open','high','low','close', 'volume']] = data[['open','high','low','close', 'volume']].astype(float) 
    return data


def _is_overbought(df: DataFrame) -> bool:
    ''' Determine if is overbought '''
    s1 = df.iloc[-1]['STOCHk_14_2_4'] < df.iloc[-1]['STOCHd_14_2_4']
    s2 = df.iloc[-2]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[-2]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
    s3 = df.iloc[-3]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[-3]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
    s4 = df.iloc[-4]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[-4]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
    return s1 and s2 and s3 and s4


def _is_oversold(df: DataFrame) -> bool:
    ''' Determine if is oversold '''
    b1 = df.iloc[-1]['STOCHk_14_2_4'] > df.iloc[-1]['STOCHd_14_2_4']
    b2 = df.iloc[-2]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-2]['STOCHd_14_2_4'] < STOCH_OVERSOLD
    b3 = df.iloc[-3]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-3]['STOCHd_14_2_4'] < STOCH_OVERSOLD
    b4 = df.iloc[-4]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-4]['STOCHd_14_2_4'] < STOCH_OVERSOLD
    return b1 and b2 and b3 and b4


def _is_turning_down(df: DataFrame) -> bool:
    ''' Determine if is turning down '''
    return df.iloc[-1]['type'] == DOWN and df.iloc[-2]['type'] == UP and df.iloc[-3]['type'] == UP and df.iloc[-4]['type'] == UP


def _is_turning_up(df: DataFrame) -> bool:
    ''' Determine if is turning up '''
    return df.iloc[-1]['type'] == UP and df.iloc[-2]['type'] == DOWN and df.iloc[-3]['type'] == DOWN and df.iloc[-4]['type'] == DOWN


# TODO: Refactor Technical Analysis to a function
def _get_renko_bricks_df(brick_size: int):
    df = get_data()
    renko = Renko(brick_size, df['close'])
    renko.create_renko()
    r_df = DataFrame(renko.bricks)

    dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
    r_df = r_df.join(dc)

    stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
    r_df = r_df.join(stoch)
    return r_df

def main ():
    while True:
        r_df = _get_renko_bricks_df(brick_size=BRICK_SIZE_10)
        
        print(r_df.tail(5), end='\n', flush=True)

        is_overbought = _is_overbought(r_df)
        is_oversold   = _is_oversold(r_df)

        is_turning_down = _is_turning_down(r_df)
        is_turning_up = _is_turning_up(r_df)

        if is_turning_down & is_overbought:
            print('SELL')
            stop_price = r_df.iloc[-2]['close'] + 10
            client.futures_create_order(symbol='BTCUSDT', side=Client.SIDE_SELL, type=Client.ORDER_TYPE_STOP_MARKET, quantity=0.001, stopPrice=stop_price)
            # TODO: Close Spot Position if exists
            orders = client.get_open_orders(symbol='BTCUSDT')
            if orders is not None:
                client.create_order(symbol='BTCUSDT', side=Client.SIDE_SELL, type=Client.ORDER_TYPE_MARKET, quantity=0.001)
                
            
        elif is_turning_up & is_oversold:
            print('BUY')
            stop_price = r_df.iloc[-2]['close'] - 10
            client.futures_create_order(symbol='BTCUSDT', side=Client.SIDE_BUY, type=Client.ORDER_TYPE_STOP_MARKET, quantity=0.001, stopPrice=stop_price)

            client.create_order(symbol='BTCUSDT', side=Client.SIDE_BUY, type=Client.ORDER_TYPE_MARKET, quantity=0.001)



        # TODO: Migrate to a service
        # That let me plot renko levels at front over Bar Charts
        # levels_df = DataFrame(detect_level_method_1(r_df))
        # [print(x) for x in detect_level_method_1(r_df)]

if __name__ == "__main__":
    # TODO: Create a Class for main loop
    while True:
        try:
            main()
        except Exception as e:
            print(e)
            continue

""" df = get_data()
renko = Renko(10, df['close'])
renko.create_renko() # renko.check_new_price(df['close'])
r_df = DataFrame(renko.bricks)

dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
r_df = r_df.join(dc)

stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
r_df = r_df.join(stoch)

print(get_signals(r_df)) """