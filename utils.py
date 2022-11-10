from pandas import DataFrame
import numpy as np
from constants import FUTURES, SPOT
from binance import Client
import math
import logging
from constants import *

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
    if market == FUTURES:
        order_book = DataFrame(client.futures_order_book(symbol=symbol, limit=10)).iloc[:,[3,4]]
    return order_book


def sell_spot_at_market(client: Client, symbol: str, quantity: float, stop_order):
    try:
        client.cancel_order(symbol=symbol, orderId=stop_order['orderId'])
        client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=quantity)
        logger.info(f"sell {symbol} {quantity}")
    except Exception as e:
        logger.error(e)


def update_spot_sl(client: Client, symbol: str, old_stop_order, new_stop_price: float, quantity: float):
    stop_order = None
    try:
        client.cancel_order(symbol=symbol, orderId=old_stop_order['orderId'])
        stop_order = client.create_order(
            symbol=symbol, 
            side=Client.SIDE_SELL, 
            type=Client.ORDER_TYPE_STOP_LOSS_LIMIT, 
            quantity=quantity, 
            price=new_stop_price, 
            stopPrice=new_stop_price, 
            timeInForce=Client.TIME_IN_FORCE_GTC
        )
        logger.info(f"update {symbol} sl {new_stop_price}")
        return stop_order
    except Exception as e:
        logger.error(e)
        return stop_order


def update_sl(client: Client, symbol: str, old_stop_order, new_stop_price: float, side: str):
    stop_order = None
    try:
        client.futures_cancel_order(symbol=symbol, orderId=old_stop_order['orderId'])
        print(side)
        stop_order = client.futures_create_order(
            symbol=symbol,
            side=side,
            type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
            stopPrice=new_stop_price,                    
            closePosition=True
        )
        logger.info(f"update {symbol} sl {new_stop_price}")
        print(stop_order)
        return stop_order
    except Exception as e:
        logger.error(e)
        return stop_order


def get_order_status(client: Client, order, market: str):
    if market == SPOT:
        return client.get_order(symbol=order['symbol'], orderId=order['orderId'])['status']
    if market == FUTURES:
        return client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])['status']


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


def _open_spot_position(self, close_price, volume):
        print('BUY')
        if self.spot_entry_order is None:
            self.spot_sl_price = round_down_price(self.client, self.symbol, close_price)
            self.spot_entry_order, _, self.spot_sl_order, _ = buy_spot_with_sl(self.client, self.symbol, volume, self.spot_sl_price)

        self.logger.debug(f'entry_order: {self.spot_entry_order}')
        self.logger.debug(f'stop_order: {self.spot_sl_order}')
        self.in_spot_position = True


def _watch_spot_position(self):
        while in_buy_position:
            r_df = self._get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True, symbol=self.symbol)        
            signal = self._get_signal(r_df)
            print('Monitoring Transaction: ...')

            if signal == SELL:
                print('Selling: ...')
                # TODO: Calculate distance between current close and entry_price to get PNL
                sell_spot_at_market(self.client, self.symbol, self.volume, stop_order)
                in_buy_position = False
                break
            else:                        
                if stop_order is not None and self.client.get_order(symbol=self.symbol, orderId=stop_order['orderId'])['status'] == 'FILLED':
                    in_buy_position = False
                    break
                
                print('Updating Stop Loss Order: ...')
                # TODO: calculate distance between entry_price and current close to get PNL
                distance_ptc = round((abs(r_df.iloc[-1]['DCM_5_5'] - r_df.iloc[-2]['close'])/r_df.iloc[-1]['DCM_5_5'])*100, 2)
                print(distance_ptc)
                if distance_ptc >= 0.1:
                    new_stop_price = r_df.iloc[-1]['DCM_5_5'] - BRICK_SIZE_10
                    stop_order = update_spot_sl(self.client, self.symbol, stop_order, new_stop_price, self.volume)



def open_position_with_sl(client: Client, symbol: str, volume: int, stop_price: float, leverage: int, side: str):
    client.futures_change_leverage(symbol=symbol, leverage=leverage)
    volume = volume * leverage
    
    order_book = get_order_book(client, symbol, FUTURES)
    for i in range(len(order_book)):
        level_price = float(order_book.iloc[i].bids[0]) if side == SELL else float(order_book.iloc[i].asks[0])
        level_liquidity = float(order_book.iloc[i].bids[1]) if side == SELL else float(order_book.iloc[i].asks[1])
        qty = round(round_down(client, symbol, (volume / level_price)), 3)
        
        logger.info(f'Trying to get best price: {level_price}')
        print(f'Trying to get best price: {level_price}')
        if qty < level_liquidity:
            entry_order = client.futures_create_order(
                symbol=symbol, 
                side=Client.SIDE_SELL if side == SELL else Client.SIDE_BUY, 
                type=Client.FUTURE_ORDER_TYPE_MARKET, 
                quantity=qty,
            )
            logger.info(f'{side} Market {entry_order}')
            print(f'{side} Market {entry_order}')   
            if entry_order is not None:
                sl_price = round_down_price(client, symbol, stop_price)
                stop_order = client.futures_create_order(
                    symbol=symbol,
                    side=Client.SIDE_BUY if side == SELL else Client.SIDE_SELL,
                    type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=sl_price,                    
                    closePosition=True
                )
                logger.info(f'{SELL if side == BUY else BUY} Stop {stop_order}')
                print(f'{SELL if side == BUY else BUY} Stop {stop_order}')                                  
            break    
    return entry_order, stop_order, level_price


def close_position_with_tp(client: Client, symbol: str, take_profit_price: float, side: str):
    return client.futures_create_order(
        symbol=symbol,
        side=Client.SIDE_BUY if side == SELL else Client.SIDE_SELL,
        type=Client.FUTURE_ORDER_TYPE_TAKE_PROFIT_MARKET,
        stopPrice=take_profit_price,                    
        closePosition=True
    )


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