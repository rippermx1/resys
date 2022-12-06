from datetime import datetime
from dotenv import load_dotenv
from pandas import DataFrame
from binance import Client
from exchange import Exchange
from database.db import Database
from models.models import Signal, Position, BotStatus
from helpers.logger import Logger
from auth.auth import Auth
from transaction import Transaction
from data import Data
from indicator import Indicator
from helpers.constants import BUY, DB_RESYS, DOWN, FUTURES, SELL, STOCHASTIC_OVERBOUGHT, STOCHASTIC_OVERSOLD, UP, DEFAULT_TRAILING_PTC
from helpers.utils import round_down_price, open_position_with_sl, get_order_status, update_sl, get_distance_ptc
load_dotenv()

class Bot:

    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        self.log = Logger()
        self.trx = Transaction()
        self.exchange = exchange
        self.symbol = symbol
        self.interval = interval
        self.volume = volume
        self.debug = debug
        self.market = market
        self.leverage = leverage
        self.brick_size = float(brick_size)
        self.trailing_ptc = float(trailing_ptc)
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

        self.data = Data(self.client, self.market, self.symbol, self.interval, self.brick_size)
        self.indicator = Indicator(self.data)

        self._start_bot_info()


    def _start_bot_info(self):
        ''' Print bot info '''
        self.log.info(f"Starting ReSys For: \nSymbol: {self.symbol}\nInterval: {self.interval}\nVolume: {self.volume}\nLeverage: {self.leverage}\nBrick Size: {self.brick_size}\nTrailing Ptc%: {self.trailing_ptc}\nPid: {self.pid}")


    def _is_stochastic_overbought(self) -> bool:
        ''' Determine if stochastic is overbought '''
        s2 = self.indicator.stochastic.iloc[-2][0] > STOCHASTIC_OVERBOUGHT and self.indicator.stochastic.iloc[-2][1] > STOCHASTIC_OVERBOUGHT
        s3 = self.indicator.stochastic.iloc[-3][0] > STOCHASTIC_OVERBOUGHT and self.indicator.stochastic.iloc[-3][1] > STOCHASTIC_OVERBOUGHT
        s4 = self.indicator.stochastic.iloc[-4][0] > STOCHASTIC_OVERBOUGHT and self.indicator.stochastic.iloc[-4][1] > STOCHASTIC_OVERBOUGHT
        return s2 and s3 and s4


    def _is_stochastic_oversold(self) -> bool:
        ''' Determine if stochastic is oversold '''
        b2 = self.indicator.stochastic.iloc[-2][0] < STOCHASTIC_OVERSOLD and self.indicator.stochastic.iloc[-2][1] < STOCHASTIC_OVERSOLD
        b3 = self.indicator.stochastic.iloc[-3][0] < STOCHASTIC_OVERSOLD and self.indicator.stochastic.iloc[-3][1] < STOCHASTIC_OVERSOLD
        b4 = self.indicator.stochastic.iloc[-4][0] < STOCHASTIC_OVERSOLD and self.indicator.stochastic.iloc[-4][1] < STOCHASTIC_OVERSOLD
        return b2 and b3 and b4


    def _is_turning_down(self) -> bool:
        ''' Determine if is turning down '''
        return self.data.renko.iloc[-1]['type'] == DOWN and self.data.renko.iloc[-2]['type'] == UP and self.data.renko.iloc[-3]['type'] == UP and self.data.renko.iloc[-4]['type'] == UP and self.data.renko.iloc[-5]['type'] == UP


    def _is_turning_up(self) -> bool:
        ''' Determine if is turning up '''
        return self.data.renko.iloc[-1]['type'] == UP and self.data.renko.iloc[-2]['type'] == DOWN and self.data.renko.iloc[-3]['type'] == DOWN and self.data.renko.iloc[-4]['type'] == DOWN and self.data.renko.iloc[-5]['type'] == DOWN


    def _close_above_dc(self) -> bool:
        ''' Determine if close is above DC '''
        mid_dc_idx = 1
        return self.data.renko.iloc[-1]['close'] > self.data.renko.iloc[-1][mid_dc_idx]


    def _close_below_dc(self) -> bool:
        ''' Determine if close is below DC '''
        mid_dc_idx = 1
        return self.data.renko.iloc[-1]['close'] < self.data.renko.iloc[-1][mid_dc_idx]


    def _get_signal(self) -> str:
        ''' Determine signal '''
        signal = None
        if self._is_turning_down() & self._is_stochastic_overbought() & self._close_below_dc():
            signal = SELL
        elif self._is_turning_up() & self._is_stochastic_oversold() & self._close_above_dc():
            signal = BUY
        if signal is not None:
            self.log.info(f'{Logger.SIGNAL_FOUND}: {signal}')            
        return signal


    def _save_signal(self, signal: Signal):
        ''' Save signal Into Database '''
        if signal.side is not None and not self.signal_saved:
            database = Database(DB_RESYS)
            database.insert_one('signal', {
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


    def _increase_trailing_ptc(self):
        ''' Increase trailing percentage '''
        self.trailing_ptc += self.trailing_ptc


    def _update_sl(self, close, avg, protection_order_side: str):
        self.log.info(f'{Logger.UPDATING_SL}')        
        distance = get_distance_ptc(self.entry_price, close)
        right_direction = (close < self.entry_price) if (protection_order_side == BUY) else (close > self.entry_price)
        sign = '+' if right_direction else '-'
        self.log.info(f'Distance: {sign}{distance}%')
        if (distance > (self.trailing_ptc * 2)) and right_direction:
            self._increase_trailing_ptc()
            self.sl_price = self._get_stop_loss_price(avg, d=1)
            self.sl_order = update_sl(self.client, self.symbol, self.sl_order, self.sl_price, protection_order_side)
            self.log.info(f'{Logger.SL_UPDATED} {self.sl_order["orderId"]}')
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
            self.log.info(f'{Logger.MONITORING_POSITION} {self.entry_order["orderId"]}')
            exit_signal = self._get_signal()
            sl_status = get_order_status(self.client, self.sl_order, FUTURES)
            self.log.info(f'{Logger.STOP_LOSS_STATUS} {sl_status}')

            # TODO: Calculate distance between current close and entry_price to get PNL
            # _get_current_pnl()
            # PnL = Close Value – Open Value = Contract Quantity x Contract Size x Close Price – Contract Quantity x Contract Size x Open Price
            pnl = self.data.renko.iloc[-1]['close'] - self.entry_price

            if self._is_time_to_take_profit(exit_signal):
                self._update_sl(self.data.renko.iloc[-1]['close'], self.data.renko.iloc[-1]['DCM_5_5'], BUY if self.signal == SELL else SELL)
                break
            else:
                if sl_status == Client.ORDER_STATUS_FILLED or sl_status == Client.ORDER_STATUS_CANCELED or sl_status == Client.ORDER_STATUS_EXPIRED:
                    self.log.info(Logger.STOP_LOSS_TRIGGERED)                    
                    self._clean_up()
                    break                
                self._update_sl(self.data.renko.iloc[-1]['close'], self.data.renko.iloc[-3]['DCM_5_5'], BUY if self.signal == SELL else SELL)


    def _open_position(self, position: Position):
        if self.market == FUTURES and not self.in_position:
            if self.entry_order is None and self.signal is not None:
                self.sl_price = self._get_stop_loss_price(position.sl_price, d=5)
                self.entry_order, self.sl_order, self.entry_price = open_position_with_sl(self.client, self.symbol, self.volume, self.sl_price, self.leverage, self.signal)
                self.trx.save(self.bot_id, self.symbol, self.market, datetime.now(), self.entry_order['entryPrice'], self.entry_order['orderType'], self.sl_order['side'], self.entry_order['orderQty'], self.sl_order['baseAsset'], self.sl_order['quoteAsset'], self.sl_order['fee'])
                self.in_position = True


    def run(self):
        self.status = self._bot_status()
        while self.status == BotStatus.RUNNING:
            self.status = self._bot_status()
            
            self.data.renko = self.data._get_renko_bricks()
            self.indicator.data = self.data
            self.indicator.stochastic = self.indicator._get_stochastic()
            self.indicator.donchian = self.indicator._get_donchian()
            
            print(f'type: {self.data.renko.iloc[-1][0]} | close: {self.data.renko.iloc[-1][2]} | stoch_K: {self.indicator.stochastic.iloc[-1][0]} | stoch_D: {self.indicator.stochastic.iloc[-1][1]} | donchian_M: {self.indicator.donchian.iloc[-1][1]}')
            self.signal = self._get_signal()
            if self.signal is None:
                continue

            self._save_signal(Signal(self.signal, datetime.now(), self.data.renko.iloc[-1]['close'], False))
            self._open_position(Position(self.signal, datetime.now(), self.data.renko.iloc[-1]['close'], False))
            self._watch_position()
