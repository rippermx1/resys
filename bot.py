from datetime import datetime
from dotenv import load_dotenv
import os
from pandas import DataFrame
from binance import Client
from renko import Renko
import pandas_ta as ta
from database import Database
from models import Signal
from logger import Logger
from constants import BRICK_SIZE_10, BUY, DATABASE_RESYS, DOWN, FUTURES, SELL, STOCHASTIC_OVERBOUGHT, STOCHASTIC_OVERSOLD, UP
from utils import buy_spot_with_sl, round_down_price, sell_spot_at_market, update_spot_sl, open_position_with_sl, get_order_status, close_position_with_tp, update_sl
load_dotenv()

class ReSys:

    def __init__(self, client, symbol, volume):
        self.logger = Logger().log
        self.client = client
        self.symbol = symbol
        self.volume = volume
        self.debug = False
        self.signal = None
        self.signal_saved = False
        self.is_live = self._is_bot_live()
        self.market = None
        self.leverage = None

        self.entry_order = None
        self.sl_order = None
        self.sl_price = None
        self.entry_price = None
        
        self.in_position = False

    def _get_data(self, hist: bool = False, start_str: str = None, symbol: str = None) -> DataFrame:
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


    def _is_overbought(self, df: DataFrame) -> bool:
        ''' Determine if is overbought '''
        s1 = df.iloc[-1]['STOCHk_14_2_4'] < df.iloc[-1]['STOCHd_14_2_4']
        s2 = df.iloc[-2]['STOCHk_14_2_4'] > STOCHASTIC_OVERBOUGHT and df.iloc[-2]['STOCHd_14_2_4'] > STOCHASTIC_OVERBOUGHT
        s3 = df.iloc[-3]['STOCHk_14_2_4'] > STOCHASTIC_OVERBOUGHT and df.iloc[-3]['STOCHd_14_2_4'] > STOCHASTIC_OVERBOUGHT
        s4 = df.iloc[-4]['STOCHk_14_2_4'] > STOCHASTIC_OVERBOUGHT and df.iloc[-4]['STOCHd_14_2_4'] > STOCHASTIC_OVERBOUGHT
        return s1 and s2 and s3 and s4


    def _is_oversold(self, df: DataFrame) -> bool:
        ''' Determine if is oversold '''
        b1 = df.iloc[-1]['STOCHk_14_2_4'] > df.iloc[-1]['STOCHd_14_2_4']
        b2 = df.iloc[-2]['STOCHk_14_2_4'] < STOCHASTIC_OVERSOLD and df.iloc[-2]['STOCHd_14_2_4'] < STOCHASTIC_OVERSOLD
        b3 = df.iloc[-3]['STOCHk_14_2_4'] < STOCHASTIC_OVERSOLD and df.iloc[-3]['STOCHd_14_2_4'] < STOCHASTIC_OVERSOLD
        b4 = df.iloc[-4]['STOCHk_14_2_4'] < STOCHASTIC_OVERSOLD and df.iloc[-4]['STOCHd_14_2_4'] < STOCHASTIC_OVERSOLD
        return b1 and b2 and b3 and b4


    def _is_turning_down(self, df: DataFrame) -> bool:
        ''' Determine if is turning down '''
        return df.iloc[-1]['type'] == DOWN and df.iloc[-2]['type'] == UP and df.iloc[-3]['type'] == UP and df.iloc[-4]['type'] == UP


    def _is_turning_up(self, df: DataFrame) -> bool:
        ''' Determine if is turning up '''
        return df.iloc[-1]['type'] == UP and df.iloc[-2]['type'] == DOWN and df.iloc[-3]['type'] == DOWN and df.iloc[-4]['type'] == DOWN


    def _close_above_dc(self, df: DataFrame) -> bool:
        ''' Determine if close is above DC '''
        return df.iloc[-1]['close'] > df.iloc[-1]['DCM_5_5']


    def _close_below_dc(self, df: DataFrame) -> bool:
        ''' Determine if close is below DC '''
        return df.iloc[-1]['close'] < df.iloc[-1]['DCM_5_5']


    def _get_renko_bricks_df(self, brick_size: int, debug: bool = False, symbol: str= None) -> DataFrame:
        self.logger.info('Building Renko Bricks')
        df = self._get_data(hist= False, start_str= None, symbol=symbol)
        renko = Renko(brick_size, df['close'])
        renko.create_renko()
        r_df = DataFrame(renko.bricks)

        dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
        r_df = r_df.join(dc)

        stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
        r_df = r_df.join(stoch)
        if debug:
            print(r_df.tail(5), end='\n', flush=True)
            self.logger.debug(r_df.tail(5))
        return r_df


    def _get_signal(self, r_df: DataFrame) -> str:
        ''' Determine signal '''
        self.logger.info('Waiting for signal')
        signal = None
        if self._is_turning_down(r_df) & self._is_overbought(r_df) & self._close_below_dc(r_df):
            signal = SELL
        elif self._is_turning_up(r_df) & self._is_oversold(r_df) & self._close_above_dc(r_df):
            signal = BUY
        return signal


    def _save_signal(self, signal: Signal):
        ''' Save signal Into Database '''
        print("Signal: {}".format(signal.side))
        if signal.side is not None and not self.signal_saved:
            self.logger.info(f'Signal: {signal}')
            database = Database()
            database.initialize(DATABASE_RESYS)
            database.insert('signal', {
                'side': signal.side, 
                'date': signal.date,
                'close': signal.close,
                'test': signal.test
            })
            self.signal_saved = True


    def _is_bot_live(self, debug: bool = False) -> bool:
        ''' Determine if bot is live '''
        database = Database()
        database.initialize(DATABASE_RESYS)
        resys_config = database.find_one('config', None)
        is_live = resys_config['is_live']
        self.logger.info(f'Is Live: {is_live}')
        if debug:
            print("is_live: {}".format(resys_config))
        return is_live


    def _clean_up(self):
        self.in_position = False
        self.signal_saved = False
        self.sl_order = None
        self.sl_price = None
        self.entry_order = None


    def _update_sl(self, renko_blocks: DataFrame, side: str):
        print('Updating Stop Loss Order: ...')
        # TODO: calculate distance between entry_price and current close to get PNL
        distance = round((abs(self.entry_price - renko_blocks.iloc[-1]['close'])/self.entry_price)*100, 2)
        print(distance)
        if distance > 0.15:
            mid = renko_blocks.iloc[-1]['DCM_5_5']
            self.sl_price = (mid - BRICK_SIZE_10) if side == BUY else (mid + BRICK_SIZE_10)
            self.sl_order = update_sl(
                self.client,
                self.symbol,
                self.sl_order,
                self.sl_price,
                side
            )
            print('Stop Loss Order Updated: {}'.format(self.sl_order))


    def _watch_position(self):
        while self.in_position:
            r_df = self._get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=True, symbol=self.symbol)        
            exit_signal = self._get_signal(r_df)
            print('Monitoring Transaction: ...')
            s = exit_signal == BUY
            d = exit_signal == SELL
            is_time_to_take_profit = s if self.signal == SELL else d
            if is_time_to_take_profit:
                print('Selling: ...')
                # TODO: Calculate distance between current close and entry_price to get PNL
                # _get_current_pnl()
                sl_price = r_df.iloc[-1]['close'] + BRICK_SIZE_10 if self.signal == SELL else r_df.iloc[-1]['close'] - BRICK_SIZE_10
                close_position_with_tp(self.client, self.symbol, sl_price)
                self._clean_up()
                break
            else:      
                status = get_order_status(self.client, self.sl_order, FUTURES)
                print(status)
                if status == 'FILLED' or status == 'CANCELED':
                    print('EXIT BY STOP LOSS')
                    self._clean_up()
                    break
                self._update_sl(r_df, SELL if self.signal == SELL else BUY)
                    


    def run(self):
        while self.is_live:
            self.is_live = self._is_bot_live()
            
            r_df = self._get_renko_bricks_df(brick_size=BRICK_SIZE_10, debug=self.debug, symbol=self.symbol)        
            self.signal = self._get_signal(r_df)
            self.signal = BUY
            self._save_signal(Signal(self.signal, datetime.now(), r_df.iloc[-1]['close'], False))            
            self._open_position(r_df)
            self._watch_position()


    def _open_spot_position(self, close_price, volume):
        print('BUY')
        if self.spot_entry_order is None:
            self.spot_sl_price = round_down_price(self.client, self.symbol, close_price)
            self.spot_entry_order, _, self.spot_sl_order, _ = buy_spot_with_sl(self.client, self.symbol, volume, self.spot_sl_price)

        self.logger.debug(f'entry_order: {self.spot_entry_order}')
        self.logger.debug(f'stop_order: {self.spot_sl_order}')
        self.in_spot_position = True


    def _open_position(self, renko_blocks: DataFrame):
        if self.market == FUTURES and not self.in_position:
            self.logger.info(f'{self.signal} signal found')
            print(self.signal)
            if self.entry_order is None:
                price = (renko_blocks.iloc[-2]['close'] + BRICK_SIZE_10) if self.signal == SELL else renko_blocks.iloc[-2]['close'] - BRICK_SIZE_10
                self.sl_price = round_down_price(self.client, self.symbol, price)
                self.entry_order, self.sl_order, self.entry_price = open_position_with_sl(self.client, self.symbol, self.volume, self.sl_price, self.leverage, self.signal)
    
                self.logger.debug(f'entry_order: {self.entry_order}')
                self.logger.debug(f'stop_order: {self.sl_order}')
                self.in_position = True


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


if __name__ == "__main__":
    client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))
    bot = ReSys(client, 'BTCUSDT', 100)
    bot.debug = True
    bot.market = FUTURES
    bot.volume = 10
    bot.leverage = 20

    while True:
        try:
            bot.run()
        except Exception as e:
            print(e)
            continue