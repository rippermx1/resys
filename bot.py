from backtest import get_signals
from dotenv import load_dotenv
import os
from pandas import DataFrame

from utils import detect_level_method_1
load_dotenv()
import asyncio
from binance import AsyncClient, BinanceSocketManager, Client
from renko import Renko
import pandas_ta as ta


def get_data():
    data = client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_5MINUTE, limit=1000)
    data = DataFrame(data)
    data = data.iloc[:,[0,1,2,3,4,5]]
    data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    data[['open','high','low','close', 'volume']] = data[['open','high','low','close', 'volume']].astype(float) 
    # data['date'] = pd.to_datetime(data['date'], unit='ms')
    return data

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
STOCH_OVERBOUGHT = 95
STOCH_OVERSOLD = 5

UP = 'up'
DOWN = 'down'

def main ():
    while True:
        df = get_data()

        renko = Renko(10, df['close'])
        renko.create_renko()
        # renko.check_new_price(df['close'])
        r_df = DataFrame(renko.bricks)

        dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
        r_df = r_df.join(dc)

        stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
        r_df = r_df.join(stoch)
        # print(get_signals(r_df))
        # print(r_df)
        print(r_df.tail(5), end='\n', flush=True)

        s1 = r_df.iloc[-1]['STOCHk_14_2_4'] < r_df.iloc[-1]['STOCHd_14_2_4']
        s2 = r_df.iloc[-2]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and r_df.iloc[-2]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s3 = r_df.iloc[-3]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and r_df.iloc[-3]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s4 = r_df.iloc[-4]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and r_df.iloc[-4]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        is_overbought = s1 and s2 and s3 and s4

        b1 = r_df.iloc[-1]['STOCHk_14_2_4'] > r_df.iloc[-1]['STOCHd_14_2_4']
        b2 = r_df.iloc[-2]['STOCHk_14_2_4'] < STOCH_OVERSOLD and r_df.iloc[-2]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b3 = r_df.iloc[-3]['STOCHk_14_2_4'] < STOCH_OVERSOLD and r_df.iloc[-3]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b4 = r_df.iloc[-4]['STOCHk_14_2_4'] < STOCH_OVERSOLD and r_df.iloc[-4]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        is_oversold = b1 and b2 and b3 and b4

        is_turning_down = r_df.iloc[-1]['type'] == DOWN and r_df.iloc[-2]['type'] == UP and r_df.iloc[-3]['type'] == UP and r_df.iloc[-4]['type'] == UP
        is_turning_up = r_df.iloc[-1]['type'] == UP and r_df.iloc[-2]['type'] == DOWN and r_df.iloc[-3]['type'] == DOWN and r_df.iloc[-4]['type'] == DOWN

        if is_turning_down & is_overbought:
            print('SELL')
        elif is_turning_up & is_oversold:
            print('BUY')

        # TODO: Migrate to a service
        # That let me plot renko levels at front over Bar Charts
        # levels_df = DataFrame(detect_level_method_1(r_df))
        # [print(x) for x in detect_level_method_1(r_df)]

main()

""" df = get_data()
renko = Renko(10, df['close'])
renko.create_renko() # renko.check_new_price(df['close'])
r_df = DataFrame(renko.bricks)

dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
r_df = r_df.join(dc)

stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
r_df = r_df.join(stoch)

print(get_signals(r_df)) """