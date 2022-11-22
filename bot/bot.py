from datetime import datetime
from dotenv import load_dotenv
from pandas import DataFrame
from binance import Client
from renko import Renko
import pandas_ta as ta
from exchange import Exchange
from database.db import Database
from models import Signal, Position
from helpers.logger import Logger
from auth.auth import Auth
from models import BotStatus
from helpers.constants import BUY, DB_RESYS, DOWN, FUTURES, SELL, STOCHASTIC_OVERBOUGHT, STOCHASTIC_OVERSOLD, UP, SPOT, DEFAULT_TRAILING_PTC
from helpers.utils import round_down_price, open_position_with_sl, get_order_status, close_position_with_tp, update_sl
load_dotenv()

class Bot:

    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        self.log = Logger()
        self.exchange = exchange
        self.symbol = symbol
        self.interval = interval
        self.volume = volume
        self.debug = debug
        self.market = market
        self.leverage = leverage
        self.brick_size = brick_size
        self.trailing_ptc = trailing_ptc
        self.pid = pid
        self.secret = secret
        self.bot_id = bot_id

        self.signal = None
        self.entry_order = None
        self.sl_order = None
        self.sl_price = None
        self.entry_price = None

        self.in_position = False
        self.signal_saved = False

        self.client = self.exchange.get_client()        
        self.status = self._bot_status()
        self._start_bot_info()


    def _start_bot_info(self):
        ''' Print bot info '''
        self.log.info(f"Starting ReSys For: \nSymbol: {self.symbol}\nInterval: {self.interval}\nVolume: {self.volume}\nLeverage: {self.leverage}\nBrick Size: {self.brick_size}\nTrailing Ptc%: {self.trailing_ptc}\nPid: {self.pid}")


    def _get_data(self, hist: bool = False, start_str: str = None) -> DataFrame:
        data = None
        if hist and self.market == SPOT:
            data = self.client.get_historical_klines(symbol=self.symbol, interval=self.interval, start_str=start_str, limit=1000)
        else:
            data = self.client.get_klines(symbol=self.symbol, interval=self.interval, limit=1000)
        
        if hist and self.market == FUTURES:
            data = self.client.futures_historical_klines(symbol=self.symbol, interval=self.interval, start_str=start_str, limit=1000)
        else:
            data = self.client.futures_klines(symbol=self.symbol, interval=self.interval, limit=1000)

        data = DataFrame(data)
        data = data.iloc[:,[0,1,2,3,4,5]]
        data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        data[['open','high','low','close', 'volume']] = data[['open','high','low','close', 'volume']].astype(float) 
        return data


    def _is_overbought(self, df: DataFrame) -> bool:
        ''' Determine if is overbought '''
        # s1 = df.iloc[-1]['STOCHk_14_2_4'] < df.iloc[-1]['STOCHd_14_2_4']
        s2 = df.iloc[-2]['STOCHk_14_2_4'] > STOCHASTIC_OVERBOUGHT and df.iloc[-2]['STOCHd_14_2_4'] > STOCHASTIC_OVERBOUGHT
        s3 = df.iloc[-3]['STOCHk_14_2_4'] > STOCHASTIC_OVERBOUGHT and df.iloc[-3]['STOCHd_14_2_4'] > STOCHASTIC_OVERBOUGHT
        s4 = df.iloc[-4]['STOCHk_14_2_4'] > STOCHASTIC_OVERBOUGHT and df.iloc[-4]['STOCHd_14_2_4'] > STOCHASTIC_OVERBOUGHT
        return s2 and s3 and s4


    def _is_oversold(self, df: DataFrame) -> bool:
        ''' Determine if is oversold '''
        # b1 = df.iloc[-1]['STOCHk_14_2_4'] > df.iloc[-1]['STOCHd_14_2_4']
        b2 = df.iloc[-2]['STOCHk_14_2_4'] < STOCHASTIC_OVERSOLD and df.iloc[-2]['STOCHd_14_2_4'] < STOCHASTIC_OVERSOLD
        b3 = df.iloc[-3]['STOCHk_14_2_4'] < STOCHASTIC_OVERSOLD and df.iloc[-3]['STOCHd_14_2_4'] < STOCHASTIC_OVERSOLD
        b4 = df.iloc[-4]['STOCHk_14_2_4'] < STOCHASTIC_OVERSOLD and df.iloc[-4]['STOCHd_14_2_4'] < STOCHASTIC_OVERSOLD
        return b2 and b3 and b4


    def _is_turning_down(self, df: DataFrame) -> bool:
        ''' Determine if is turning down '''
        return df.iloc[-1]['type'] == DOWN and df.iloc[-2]['type'] == DOWN and df.iloc[-3]['type'] == UP and df.iloc[-4]['type'] == UP and df.iloc[-5]['type'] == UP


    def _is_turning_up(self, df: DataFrame) -> bool:
        ''' Determine if is turning up '''
        return df.iloc[-1]['type'] == UP and df.iloc[-2]['type'] == UP and df.iloc[-3]['type'] == DOWN and df.iloc[-4]['type'] == DOWN and df.iloc[-5]['type'] == DOWN


    def _close_above_dc(self, df: DataFrame) -> bool:
        ''' Determine if close is above DC '''
        return df.iloc[-1]['close'] > df.iloc[-1]['DCM_5_5']


    def _close_below_dc(self, df: DataFrame) -> bool:
        ''' Determine if close is below DC '''
        return df.iloc[-1]['close'] < df.iloc[-1]['DCM_5_5']


    def _get_renko_bricks_df(self) -> DataFrame:
        self.log.info(Logger.BUILDING_BRICKS)
        df = self._get_data()
        renko = Renko(self.brick_size, df['close'])
        renko.create_renko()
        r_df = DataFrame(renko.bricks)

        dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
        r_df = r_df.join(dc)

        stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
        r_df = r_df.join(stoch)
        if self.debug:
            self.log.debug(r_df.tail(5))            
        return r_df


    def _get_signal(self, r_df: DataFrame) -> str:
        ''' Determine signal '''
        signal = None
        if self._is_turning_down(r_df) & self._is_overbought(r_df) & self._close_below_dc(r_df):
            signal = SELL
        elif self._is_turning_up(r_df) & self._is_oversold(r_df) & self._close_above_dc(r_df):
            signal = BUY
        if signal is not None:
            self.log.info(f'{Logger.SIGNAL_FOUND}: {signal}')            
        return signal


    def _save_signal(self, signal: Signal):
        ''' Save signal Into Database '''
        if signal.side is not None and not self.signal_saved:
            database = Database(DB_RESYS)
            database.insert('signal', {
                'side': signal.side, 
                'date': signal.date,
                'close': signal.close,
                'test': signal.test
            })
            self.signal_saved = True
            self.log.info('Signal Saved')


    def _bot_status(self):
        auth = Auth(secret=self.secret)
        user_bot = auth.get_bot(self.bot_id)
        return user_bot['status']


    def _clean_up(self):
        ''' Restore Default Values for the Bot in order to keep running '''
        self.in_position = False
        self.signal_saved = False
        self.sl_order = None
        self.sl_price = None
        self.entry_order = None
        self.trailing_ptc = DEFAULT_TRAILING_PTC


    def _get_distance_ptc(self, a, b)-> float:
        ''' Get distance between two points in percentage '''
        return round( (abs(a - b) / a) * 100, 2)


    def _increase_trailing_ptc(self):
        ''' Increase trailing percentage '''
        self.trailing_ptc += self.trailing_ptc


    def _update_sl(self, close, avg, protection_order_side: str):
        self.log.info('Updating Stop Loss Order')        
        # TODO: calculate distance between entry_price and current close to get PNL
        distance = self._get_distance_ptc(self.entry_price, close)
        self.log.info(f'Distance: {distance}%')
        right_direction = (close < self.entry_price) if (protection_order_side == BUY) else (close > self.entry_price)
        self.log.info(f'Direction: {right_direction}')
        if (distance > self.trailing_ptc) and right_direction:
            self._increase_trailing_ptc()
            self.sl_price = self._get_stop_loss_price(avg, d=2)
            self.sl_order = update_sl(self.client, self.symbol, self.sl_order, self.sl_price, protection_order_side)
            self.log.info('Stop Loss Order Updated: {}'.format(self.sl_order))
            if self.sl_order is None:
                self._clean_up()          


    def _is_time_to_take_profit(self, signal: str)-> bool:
        ''' Determine if is time to take profit by a given signal '''
        is_buy = signal == BUY
        is_sell = signal == SELL
        return is_buy if (self.signal == SELL) else is_sell


    def _get_stop_loss_price(self, price, d):
        ''' Get Stop Loss Price based on Signal Side and apply a Delta (d) Factor Stop Distance '''
        sl_price = (price + self.brick_size * d) if (self.signal == SELL) else (price - self.brick_size * d)
        return round_down_price(self.client, self.symbol, sl_price)

    def _watch_position(self):
        while self.in_position:
            self.log.info(f'Monitoring Position: {self.entry_order["orderId"]}')
            r_df = self._get_renko_bricks_df()        
            exit_signal = self._get_signal(r_df)
            
            if self._is_time_to_take_profit(exit_signal):
                # TODO: Calculate distance between current close and entry_price to get PNL
                # _get_current_pnl()
                close_position_with_tp(self.client, self.symbol, self._get_stop_loss_price(r_df.iloc[-1]['close'], d=3), BUY if (self.signal == SELL) else SELL)
                self._clean_up()
                break
            else:      
                sl_status = get_order_status(self.client, self.sl_order, FUTURES)
                self.log.info(f'Stop Loss Status: {sl_status}')
                if sl_status == Client.ORDER_STATUS_FILLED or sl_status == Client.ORDER_STATUS_CANCELED or sl_status == Client.ORDER_STATUS_EXPIRED:
                    self.log.info(Logger.STOP_LOSS_TRIGGERED)                    
                    self._clean_up()
                    break                
                self._update_sl(r_df.iloc[-1]['close'], r_df.iloc[-2]['DCM_5_5'], BUY if self.signal == SELL else SELL)


    def _open_position(self, position: Position):
        if self.market == FUTURES and not self.in_position:
            if self.entry_order is None and self.signal is not None:
                self.sl_price = self._get_stop_loss_price(position.sl_price, d=3)
                self.entry_order, self.sl_order, self.entry_price = open_position_with_sl(self.client, self.symbol, self.volume, self.sl_price, self.leverage, self.signal)
                self.in_position = True


    def run(self):
        self.status = self._bot_status()
        while self.status == BotStatus.RUNNING:
            self.log.info(Logger.WAITING_SIGNAL)
            self.status = self._bot_status()
            r_df = self._get_renko_bricks_df()
            self.signal = self._get_signal(r_df)            
            self._save_signal(Signal(self.signal, datetime.now(), r_df.iloc[-1]['close'], False))            
            self._open_position(Position(self.signal, datetime.now(), r_df.iloc[-3]['close'], False))
            self._watch_position()

