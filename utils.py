from typing import Dict
from pandas import DataFrame
import numpy as np
from constants import SPOT, FUTURE
from binance import Client
import math
import logging

logging.basicConfig(filename="./std.log", 
					format='%(asctime)s %(message)s', 
					filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

# to make sure the new level area does not exist already
def is_far_from_level( value, levels, df: DataFrame):    
    ave =  np.mean(abs(df['open'] - df['close']))    
    return np.sum([abs(value-level)<ave for _,level in levels])==0

# determine bullish fractal 
def is_support( df: DataFrame, i) -> bool:  
    cond1 = df['close'][i] < df['close'][i-1]   
    cond2 = df['close'][i] < df['close'][i+1]   
    cond3 = df['close'][i+1] < df['close'][i+2]   
    cond4 = df['close'][i-1] < df['close'][i-2]  
    return (cond1 and cond2 and cond3 and cond4)

# determine bearish fractal
def is_resistance( df: DataFrame, i) -> bool:  
    cond1 = df['close'][i] > df['close'][i-1]   
    cond2 = df['close'][i] > df['close'][i+1]   
    cond3 = df['close'][i+1] > df['close'][i+2]   
    cond4 = df['close'][i-1] > df['close'][i-2]  
    return (cond1 and cond2 and cond3 and cond4)

#method 1: fractal candlestick pattern
def detect_level_method_1( df: DataFrame):
    shift = 2
    levels = []
    parsed = []
    for i in range(shift, df.shape[0] - shift):
        l = df['close'][i]
        if is_support(df, i):
            if is_far_from_level(l, levels, df):
                levels.append((df.index[i], l))
                parsed.append({
                    'time': df.index[i], 
                    'value': l,
                    'type': 'support'
                    })
        elif is_resistance(df, i):
            if is_far_from_level(l, levels, df):
                levels.append((df.index[i], l))
                parsed.append({
                    'time': df.index[i], 
                    'value': l,
                    'type': 'resistance'
                    })
    return parsed    

#method 2: window shifting method
def detect_level_method_2( df):
    levels = []
    max_list = []
    min_list = []
    parsed = []
    for i in range(5, len(df)-5):
        high_range = df['High'][i-5:i+4]
        current_max = high_range.max()
        if current_max not in max_list:
            max_list = []
        max_list.append(current_max)
        if len(max_list) == 5 and is_far_from_level(current_max, levels, df):
            levels.append((high_range.idxmax(), current_max))
            parsed.append({
                    'time': high_range.idxmax(), 
                    'value': current_max,
                    'type': 'resistance'
                    })
        
        low_range = df['Low'][i-5:i+5]
        current_min = low_range.min()
        if current_min not in min_list:
            min_list = []
        min_list.append(current_min)
        if len(min_list) == 5 and is_far_from_level(current_min, levels, df):
            levels.append((low_range.idxmin(), current_min))
            parsed.append({
                    'time': low_range.idxmin(), 
                    'value': current_min,
                    'type': 'support'
                    })
    return parsed


def round_down(client: Client, symbol, number):
    info = client.get_symbol_info(symbol=symbol)
    step_size = [float(_['stepSize']) for _ in info['filters'] if _['filterType'] == 'LOT_SIZE'][0]
    step_size = '%.8f' % step_size
    step_size = step_size.rstrip('0')
    decimals = len(step_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


def round_down_price(client: Client, symbol, number):
    info = client.get_symbol_info(symbol=symbol)
    tick_size = [float(_['tickSize']) for _ in info['filters'] if _['filterType'] == 'PRICE_FILTER'][0]
    tick_size = '%.8f' % tick_size
    tick_size = tick_size.rstrip('0')
    decimals = len(tick_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


def get_balance(client: Client):
    return float([i for i in client.get_account()['balances'] if i['asset'] == 'USDT'][0]['free'])


def get_order_book(client: Client, symbol: str, market: str) -> DataFrame:
    order_book = None
    if market == SPOT:
        order_book = DataFrame(client.get_order_book(symbol=symbol, limit=10))
    elif market == FUTURE:
        order_book = DataFrame(client.futures_order_book(symbol=symbol, limit=10))
    return order_book


def buy_spot_with_sl(client: Client, symbol: str, volume: int, stop_price: float):
    entry_order = None
    stop_order = None
    qty_to_buy = 0
    qty_to_sell = 0
    logger.info("Checking balance")
    balance = get_balance(client)
    print(balance)
    if balance < volume:
        logger.info("Not enough balance to buy")
        print("Not enough balance to buy")
        return entry_order, qty_to_buy, stop_order, qty_to_sell

    
    logger.info("Checking Order Book")
    order_book = get_order_book(client, symbol, SPOT)
    for i in range(len(order_book)):
        ask_price = float(order_book.iloc[i].asks[0])
        ask_liquidity = float(order_book.iloc[i].asks[1])
        qty_to_buy = round_down(client, symbol, (volume / ask_price))
        logger.info(f'Trying to get best price: {ask_price}')   
        if qty_to_buy < ask_liquidity:
            logger.info(f'Buying {symbol} at SPOT with Volume={volume}USDT at Price {ask_price}')
            entry_order = client.create_order(
                symbol=symbol, 
                side=Client.SIDE_BUY, 
                type=Client.ORDER_TYPE_LIMIT, 
                quantity=qty_to_buy, 
                timeInForce=Client.TIME_IN_FORCE_GTC, 
                price=ask_price
            )
            print("entry_order {}".format(entry_order))      
            if entry_order is not None:
                qty_to_sell = round_down(client, symbol, float(entry_order["fills"][0]["qty"])-float(entry_order["fills"][0]["commission"]))                    
                sl_price = round_down_price(client, symbol, stop_price)
                logger.info(f'Stop Sell {symbol} at SPOT with Volume={qty_to_sell}BTC at Price {sl_price}')
                stop_order = client.create_order(
                    symbol=symbol, 
                    side=Client.SIDE_SELL, 
                    type=Client.ORDER_TYPE_STOP_LOSS_LIMIT, 
                    quantity=qty_to_sell, 
                    price=sl_price, 
                    stopPrice=sl_price, 
                    timeInForce=Client.TIME_IN_FORCE_GTC
                )
                print("stop_order {}".format(stop_order))                                    
            break               
    return entry_order, qty_to_buy, stop_order, qty_to_sell


def get_klines_history(client: Client, symbol: str, interval: str, start_time: int, end_time: int):
    klines = client.get_historical_klines(symbol=symbol, interval=interval, start_str=start_time, end_str=end_time)
    df = DataFrame(klines, columns=['open_time', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['open_time'] = df['open_time'].astype('datetime64[ms]')
    df['close_time'] = df['close_time'].astype('datetime64[ms]')
    df['open'] = df['open'].astype('float')
    df['high'] = df['high'].astype('float')
    df['low'] = df['low'].astype('float')
    df['close'] = df['close'].astype('float')
    df['volume'] = df['volume'].astype('float')
    df.set_index('open_time', inplace=True)
    return df