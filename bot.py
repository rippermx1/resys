from datetime import datetime
from dotenv import load_dotenv
import os
from pandas import DataFrame
from binance import Client
from renko import Renko
import pandas_ta as ta
import logging
from database import Database
from models import Signal

logging.basicConfig(filename="./std.log", 
					format='%(asctime)s %(message)s', 
					filemode='w')
logger=logging.getLogger()
logger.setLevel(logging.DEBUG)

from constants import BRICK_SIZE_10, BUY, DOWN, SELL, STOCH_OVERBOUGHT, STOCH_OVERSOLD, UP
from utils import buy_spot_with_sl, round_down_price, sell_spot_at_market, update_spot_sl, sell_future_with_sl

load_dotenv()

database = Database()
database.initialize('resys')
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
symbol='BTCUSDT'
volume = 100 #USD

def _get_data(hist: bool = False, start_str: str = None, symbol: str = None) -> DataFrame:
    data = None
    if hist:
        data = client.get_historical_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, start_str=start_str, limit=1000)
    else:
        data = client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=1000)
    
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


def _close_above_dc(df: DataFrame) -> bool:
    ''' Determine if close is above DC '''
    return df.iloc[-1]['close'] > df.iloc[-1]['DCM_5_5']


def _close_below_dc(df: DataFrame) -> bool:
    ''' Determine if close is below DC '''
    return df.iloc[-1]['close'] < df.iloc[-1]['DCM_5_5']


# TODO: Refactor Technical Analysis to a function
def _get_renko_bricks_df(brick_size: int, debug: bool = False, symbol: str= None) -> DataFrame:
    logger.info('Building Renko Bricks')
    df = _get_data(hist= False, start_str= None, symbol=symbol)
    renko = Renko(brick_size, df['close'])
    renko.create_renko()
    r_df = DataFrame(renko.bricks)

    dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
    r_df = r_df.join(dc)

    stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
    r_df = r_df.join(stoch)
    if debug:
        print(r_df.tail(5), end='\n', flush=True)
        logger.debug(r_df.tail(5))
    return r_df


def _get_signal(r_df: DataFrame) -> str:
    ''' Determine signal '''
    logger.info('Waiting for signal')
    signal = None
    if _is_turning_down(r_df) & _is_overbought(r_df) & _close_below_dc(r_df):
        signal = SELL
    elif _is_turning_up(r_df) & _is_oversold(r_df) & _close_above_dc(r_df):
        signal = BUY
    return signal


def _save_signal(s: Signal):
    ''' Save signal Into Database '''
    logger.info(f'Signal: {s}')
    print("Signal: {}".format(s))
    database.insert('signal', {
        'side': s.side, 
        'date': s.date,
        'close': s.close,
        'test': s.test
    })


def run(symbol):
    global in_buy_position
    in_buy_position = False
    global in_sell_position
    in_sell_position = True
    entry_order = None
    stop_order = None
    qty_to_sell = 30
    stop_price = 0
    global signal
    signal = None

    # TODO: Get is_live from DB
    resys_config = database.find_one('config', None)
    is_live = resys_config['is_live']
    while is_live:
        r_df = _get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True, symbol=symbol)        
        signal = _get_signal(r_df)

        if signal is not None:
            print(signal)
            _save_signal(Signal(signal, datetime.now(), r_df.iloc[-1]['close'], False))            
        
        if signal == SELL and not in_sell_position:
            logger.info('SELL signal found')
            print('SELL')

            if entry_order is None:
                stop_price = round_down_price(client, symbol, r_df.iloc[-2]['close'] + BRICK_SIZE_10)
                entry_order, stop_order = sell_future_with_sl(client, symbol, qty_to_sell, stop_price)
            
            logger.debug(f'entry_order: {entry_order}')
            logger.debug(f'stop_order: {stop_order}')
            in_sell_position = True
            
        if signal == BUY and not in_buy_position:
            logger.info('BUY signal found')
            print('BUY')
            if entry_order is None:
                stop_price = round_down_price(client, symbol, r_df.iloc[-2]['close'] - BRICK_SIZE_10)
                entry_order, _, stop_order, qty_to_sell = buy_spot_with_sl(client, symbol, volume, stop_price)

            logger.debug(f'entry_order: {entry_order}')
            logger.debug(f'stop_order: {stop_order}')
            in_buy_position = True

        if entry_order is not None and entry_order['status'] == 'FILLED' and in_buy_position:                
            while in_buy_position:
                r_df = _get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True, symbol=symbol)        
                signal = _get_signal(r_df)
                print('Monitoring Transaction: ...')

                if signal == SELL:
                    print('Selling: ...')
                    # TODO: Calculate distance between current close and entry_price to get PNL
                    sell_spot_at_market(client, symbol, qty_to_sell, stop_order)
                    in_buy_position = False
                    break
                else:                        
                    if stop_order is not None and client.get_order(symbol=symbol, orderId=stop_order['orderId'])['status'] == 'FILLED':
                        in_buy_position = False
                        break
                    
                    print('Updating Stop Loss Order: ...')
                    # TODO: calculate distance between entry_price and current close to get PNL
                    distance_ptc = round((abs(r_df.iloc[-1]['DCM_5_5'] - r_df.iloc[-2]['close'])/r_df.iloc[-1]['DCM_5_5'])*100, 2)
                    print(distance_ptc)
                    if distance_ptc >= 0.1:
                        new_stop_price = r_df.iloc[-1]['DCM_5_5'] - BRICK_SIZE_10
                        stop_order = update_spot_sl(client, symbol, stop_order, new_stop_price, qty_to_sell)        


if __name__ == "__main__":
    # TODO: Create a Class for main loop
    # TODO: Integrate kwargs for main loop (e.g. symbol, volume, brick_size, etc.)
    
    while True:
        try:
            run(symbol)
        except Exception as e:
            print(e)
            continue


def backtest(df: DataFrame, lookback: int = 15):
    ''' Backtest '''
    in_short_position = False
    in_long_position = False
    signal = None
    win, loss = 0, 0
    for i in range(lookback, len(df)):
        # print(df.iloc[i])
        is_turning_down = df.iloc[i]['type'] == DOWN and df.iloc[i-1]['type'] == UP and df.iloc[i-2]['type'] == UP and df.iloc[i-3]['type'] == UP
        is_turning_up = df.iloc[i]['type'] == UP and df.iloc[i-1]['type'] == DOWN and df.iloc[i-2]['type'] == DOWN and df.iloc[i-3]['type'] == DOWN

        s1 = df.iloc[i]['STOCHk_14_2_4'] < df.iloc[i]['STOCHd_14_2_4']
        s2 = df.iloc[i-1]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-1]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s3 = df.iloc[i-2]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-2]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s4 = df.iloc[i-3]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-3]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        is_overbought = s1 and s2 and s3 and s4

        close_above_dc = df.iloc[i]['close'] > df.iloc[i]['DCM_5_5']
        close_under_dc = df.iloc[i]['close'] < df.iloc[i]['DCM_5_5']
        
        b1 = df.iloc[i]['STOCHk_14_2_4'] > df.iloc[i]['STOCHd_14_2_4']
        b2 = df.iloc[i-1]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-1]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b3 = df.iloc[i-2]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-2]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b4 = df.iloc[i-3]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-3]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        is_oversold = b1 and b2 and b3 and b4

        if is_turning_down and is_overbought and close_under_dc and not in_short_position:
            in_short_position = True
            in_long_position = False
            
            signal = {
                'side': 'SELL',
                'entry_price': df.iloc[i]['close'],
                'sl': df.iloc[i-1]['close'] + 20,
                'tp': df.iloc[i-1]['close'] - 80,
            }
            print(f'SELL {signal}')
                
        if is_turning_up and is_oversold and close_above_dc and not in_long_position:
            in_short_position = False
            in_long_position = True
            
            signal = {
                'side': 'BUY',
                'entry_price': df.iloc[i]['close'],
                'sl': df.iloc[i-1]['close'] - 20,
                'tp': df.iloc[i-1]['close'] + 80,
            }
            print(f'BUY {signal}')

        if in_short_position:
            if df.iloc[i]['close'] >= signal['sl']:
                in_short_position = False
                loss += 1
                print(f'STOP {df.iloc[i].close}')                            
                
            elif df.iloc[i]['close'] <= signal['tp']:
                in_short_position = False
                win += 1
                print(f'PROFIT {df.iloc[i].close}')   
        if in_long_position:
            if df.iloc[i]['close'] <= signal['sl']:
                in_short_position = False
                loss += 1
                print(f'STOP {df.iloc[i].close}')                            
                
            elif df.iloc[i]['close'] >= signal['tp']:
                in_short_position = False
                win += 1
                print(f'PROFIT {df.iloc[i].close}')                            
    print(f'win: {win} | loss: {loss}')