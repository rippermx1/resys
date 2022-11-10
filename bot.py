from datetime import datetime
from dotenv import load_dotenv
from pandas import DataFrame
from binance import Client
from renko import Renko
import pandas_ta as ta
from exchange import Exchange
from database import Database
from models import Signal, Position
from logger import Logger
from constants import BUY, DB_RESYS, DOWN, FUTURES, SELL, STOCHASTIC_OVERBOUGHT, STOCHASTIC_OVERSOLD, UP
from utils import buy_spot_with_sl, round_down_price, sell_spot_at_market, update_spot_sl, open_position_with_sl, get_order_status, close_position_with_tp, update_sl
load_dotenv()

class ReSys:

    def __init__(self, exchange: Exchange, symbol, volume, market, leverage, brick_size, debug):
        self.logger = Logger().log
        self.exchange = exchange
        self.symbol = symbol
        self.volume = volume
        self.debug = debug
        self.market = market
        self.leverage = leverage
        self.brick_size = brick_size

        self.signal = None
        self.entry_order = None
        self.sl_order = None
        self.sl_price = None
        self.entry_price = None

        self.in_position = False
        self.signal_saved = False

        self.client = self.exchange.get_client()
        self.is_live = self._is_bot_live()

    def _get_data(self, hist: bool = False, start_str: str = None) -> DataFrame:
        data = None
        if hist:
            data = self.client.get_historical_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_5MINUTE, start_str=start_str, limit=1000)
        else:
            data = self.client.get_klines(symbol=self.symbol, interval=Client.KLINE_INTERVAL_5MINUTE, limit=1000)
        
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
        self.logger.info('Building Renko Bricks')
        df = self._get_data(hist= False, start_str= None)
        renko = Renko(self.brick_size, df['close'])
        renko.create_renko()
        r_df = DataFrame(renko.bricks)

        dc = DataFrame(ta.donchian(high=r_df['close'], low=r_df['close'] ,lower_length=5, upper_length=5)).drop(columns=['DCL_5_5', 'DCU_5_5'])
        r_df = r_df.join(dc)

        stoch = DataFrame(ta.stoch(high=r_df['close'], low=r_df['close'] ,close=r_df['close'], k=14, d=2, smooth_k=4))
        r_df = r_df.join(stoch)
        if self.debug:
            print(r_df.tail(5), end='\n', flush=True)
            self.logger.debug(r_df.tail(5))
        return r_df


    def _get_signal(self, r_df: DataFrame) -> str:
        ''' Determine signal '''
        signal = None
        if self._is_turning_down(r_df) & self._is_overbought(r_df) & self._close_below_dc(r_df):
            signal = SELL
        elif self._is_turning_up(r_df) & self._is_oversold(r_df) & self._close_above_dc(r_df):
            signal = BUY
        if signal is not None:
            self.logger.info('Signal Found: {}'.format(signal))
            print('Signal Found: {}'.format(signal))
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
            self.logger.info('Signal Saved')
            print('Signal Saved')
            self.signal_saved = True


    def _is_bot_live(self, debug: bool = False) -> bool:
        ''' Determine if bot is live '''
        database = Database(DB_RESYS)
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
        self.logger.info('Updating Stop Loss Order')
        print('Updating Stop Loss Order')
        # TODO: calculate distance between entry_price and current close to get PNL
        distance = round((abs(self.entry_price - renko_blocks.iloc[-1]['close'])/self.entry_price)*100, 3)
        self.logger.info(f'Distance: {distance}%')
        print(f'Distance: {distance}%')
        if distance > 0.25:
            mid = renko_blocks.iloc[-1]['DCM_5_5']
            self.sl_price = round_down_price(self.client, self.symbol, (mid - self.brick_size) if side == SELL else (mid + self.brick_size))
            self.sl_order = update_sl(
                self.client,
                self.symbol,
                self.sl_order,
                self.sl_price,
                side
            )
            self.logger.info('Stop Loss Order Updated: {}'.format(self.sl_order))
            print('Stop Loss Order Updated: {}'.format(self.sl_order))


    def _watch_position(self):
        while self.in_position:
            print(f'Monitoring Position: {self.signal}')
            r_df = self._get_renko_bricks_df()        
            exit_signal = self._get_signal(r_df)
            
            is_buy = exit_signal == BUY
            is_sell = exit_signal == SELL
            is_time_to_take_profit = is_buy if self.signal == SELL else is_sell
            
            if is_time_to_take_profit:
                # TODO: Calculate distance between current close and entry_price to get PNL
                # _get_current_pnl()
                sl_price = r_df.iloc[-1]['close'] + self.brick_size if self.signal == SELL else r_df.iloc[-1]['close'] - self.brick_size
                sl_price = round_down_price(self.client, self.symbol, sl_price)
                close_position_with_tp(self.client, self.symbol, sl_price, BUY if self.signal == SELL else SELL)
                self._clean_up()
                break
            else:      
                sl_status = get_order_status(self.client, self.sl_order, FUTURES)
                self.logger.info(f'Stop Loss Status {sl_status}')
                print(f'Stop Loss Status {sl_status}')
                if sl_status == 'FILLED' or sl_status == 'CANCELED':
                    self.logger.info('Stop Loss Triggered')
                    print('Stop Loss Triggered')
                    self._clean_up()
                    break
                self._update_sl(r_df, BUY if self.signal == SELL else SELL)


    def _open_position(self, position: Position):
        if self.market == FUTURES and not self.in_position:
            if self.entry_order is None and self.signal is not None:
                # TODO: Calculate Stop Loss Price based on distance between entry_price and prev 2 closes plus brick_size with factor
                _sl_price = (position.sl_price + self.brick_size * 2) if self.signal == SELL else (position.sl_price - self.brick_size * 2)
                self.sl_price = round_down_price(self.client, self.symbol, _sl_price)
                self.entry_order, self.sl_order, self.entry_price = open_position_with_sl(self.client, self.symbol, self.volume, self.sl_price, self.leverage, self.signal)
                self.in_position = True


    def run(self):
        while self.is_live:
            self.logger.info('ReSys is looking for a signal... wait')
            print('ReSys is looking for a signal... wait')
            self.is_live = self._is_bot_live()
            r_df = self._get_renko_bricks_df()
            self.signal = self._get_signal(r_df)
            # self.signal = BUY
            self._save_signal(Signal(self.signal, datetime.now(), r_df.iloc[-1]['close'], False))            
            self._open_position(Position(self.signal, r_df.iloc[-2]['close'], datetime.now(), False))
            
            self._watch_position()

