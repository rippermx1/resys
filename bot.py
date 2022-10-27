from datetime import datetime
from backtest import get_signals
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

from constants import BRICK_SIZE_10, BUY, DOWN, SELL, SPOT, STOCH_OVERBOUGHT, STOCH_OVERSOLD, UP
from utils import buy_spot_with_sl, round_down_price

load_dotenv()

database = Database()
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
symbol='BTCUSDT'
volume = 100 #USD

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


def _close_above_dc(df: DataFrame) -> bool:
    ''' Determine if close is above DC '''
    return df.iloc[-1]['close'] > df.iloc[-1]['DCM_5_5']


def _close_below_dc(df: DataFrame) -> bool:
    ''' Determine if close is below DC '''
    return df.iloc[-1]['close'] < df.iloc[-1]['DCM_5_5']


# TODO: Refactor Technical Analysis to a function
def _get_renko_bricks_df(brick_size: int, debug: bool = False) -> DataFrame:
    logger.info('Building Renko Bricks')
    df = get_data()
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


def run():
    entry_order = None
    stop_order = None
    qty_to_sell = 0
    stop_price = 0
    while True:
        r_df = _get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True)        
        signal = _get_signal(r_df)

        if signal is not None:
            _save_signal(Signal(signal, datetime.now(), r_df.iloc[-1]['close'], False))            
        
        if signal == SELL:
            logger.info('SELL signal found')
            print('SELL')
            stop_price = round_down_price(client, symbol, r_df.iloc[-2]['close'] + BRICK_SIZE_10)
            if entry_order is None:
                client.futures_change_leverage(symbol=symbol, leverage=1)
                entry_order = client.futures_create_order(
                    symbol=symbol, 
                    side=Client.SIDE_SELL, 
                    type=Client.FUTURE_ORDER_TYPE_MARKET, 
                    quantity=qty_to_sell,
                    timeInForce=Client.TIME_IN_FORCE_GTC             
                )
                stop_order = client.futures_create_order(
                    symbol=symbol,
                    side=Client.SIDE_BUY,
                    type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
                    stopPrice=stop_price,
                    timeInForce=Client.TIME_IN_FORCE_GTC,
                    closePosition=True
                )
            
            print(f'entry_order: {entry_order}')
            print(f'stop_order: {stop_order}')
            logger.debug(f'entry_order: {entry_order}')
            logger.debug(f'stop_order: {stop_order}')
            if entry_order is not None and entry_order['status'] == 'FILLED':
                while True:
                    r_df = _get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True)        
                    signal = _get_signal(r_df)
                    
                    if signal == BUY:
                        client.cancel_order(symbol=symbol, orderId=stop_order['orderId'])
                        client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty_to_sell)
                        break
                    else:
                        if stop_order is not None and stop_order['status'] == 'FILLED':
                            break

                        stop_price = r_df['DCM_5_5'][-1] + BRICK_SIZE_10
                        client.cancel_order(symbol=symbol, orderId=stop_order['orderId'])
                        stop_order = client.futures_create_order(
                            symbol=symbol,
                            side=Client.SIDE_BUY,
                            type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
                            stopPrice=stop_price,
                            timeInForce=Client.TIME_IN_FORCE_GTC,
                            closePosition=True
                        )
            
        elif signal == BUY:
            logger.info('BUY signal found')
            print('BUY')
            stop_price = round_down_price(client, symbol, r_df.iloc[-2]['close'] - BRICK_SIZE_10)
            if entry_order is None:
                logger.info('Trying to buy at best price as possible')
                entry_order, _, stop_order, qty_to_sell = buy_spot_with_sl(client, symbol, volume, stop_price)

            print(f'entry_order: {entry_order}')
            print(f'stop_order: {stop_order}')
            logger.debug(f'entry_order: {entry_order}')
            logger.debug(f'stop_order: {stop_order}')
            if entry_order is not None and entry_order['status'] == 'FILLED':
                while True:
                    r_df = _get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True)        
                    signal = _get_signal(r_df)
                    
                    if signal == SELL:
                        client.cancel_order(symbol=symbol, orderId=stop_order['orderId'])
                        client.create_order(symbol=symbol, side="SELL", type="MARKET", quantity=qty_to_sell)
                        break
                    else:
                        if stop_order is not None and stop_order['status'] == 'FILLED':
                            break

                        stop_price = r_df['DCM_5_5'][-1] - BRICK_SIZE_10
                        client.cancel_order(symbol=symbol, orderId=stop_order['orderId'])
                        stop_order = client.create_order(
                            symbol=symbol, 
                            side=Client.SIDE_SELL, 
                            type=Client.ORDER_TYPE_STOP_LOSS_LIMIT, 
                            quantity=qty_to_sell, 
                            price=stop_price, 
                            stopPrice=stop_price, 
                            timeInForce=Client.TIME_IN_FORCE_GTC
                        )                                                                        


if __name__ == "__main__":
    # TODO: Create a Class for main loop
    # TODO: Integrate kwargs for main loop (e.g. symbol, volume, brick_size, etc.)
    while True:
        try:
            run()                   
        except Exception as e:
            print(e)
            continue


def backtest(df: DataFrame, lookback: int = 15):
    ''' Backtest '''

    for i in range(lookback, len(df)):
        is_turning_down = df.iloc[i]['type'] == DOWN and df.iloc[i-1]['type'] == UP and df.iloc[i-2]['type'] == UP and df.iloc[i-3]['type'] == UP
        is_turning_up = df.iloc[i]['type'] == UP and df.iloc[i-1]['type'] == DOWN and df.iloc[i-2]['type'] == DOWN and df.iloc[i-3]['type'] == DOWN

        s1 = df.iloc[i]['STOCHk_14_2_4'] < df.iloc[i]['STOCHd_14_2_4']
        s2 = df.iloc[i-1]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-1]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s3 = df.iloc[i-2]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-2]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s4 = df.iloc[i-3]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-3]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        is_overbought = s1 and s2 and s3 and s4

        b1 = df.iloc[i]['STOCHk_14_2_4'] > df.iloc[i]['STOCHd_14_2_4']
        b2 = df.iloc[i-1]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-1]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b3 = df.iloc[i-2]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-2]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b4 = df.iloc[i-3]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-3]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        is_oversold = b1 and b2 and b3 and b4

        if is_turning_down and is_overbought:
            print('SELL')
        if is_turning_up and is_oversold:
            print('BUY')

