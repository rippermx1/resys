from core.bot import Bot
from core.exchange import Exchange
from datetime import datetime
from models.models import BotStatus
from helpers.logger import Logger
from helpers.constants import BUY, SELL, FUTURES, DB_RESYS
from helpers.utils import get_distance_ptc
from database.db import Database


class StochasticDonchian(Bot):


    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        super().__init__(exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid)
        self.stochastic.smooth_k = 21
        self.stochastic.k = 100
        self.stochastic.d = 2
        self.donchian.length = 6


    def get_signal(self) -> str:
        ''' Determine signal '''
        signal = None
        if self.data.is_turning_down() & self.stochastic.is_overbought() & self.donchian.close_below_mid():
            signal = SELL
        elif self.data.is_turning_up() & self.stochastic.is_oversold() & self.donchian.close_above_mid():
            signal = BUY
        if signal is not None:
            self.log.info(f'{Logger.SIGNAL_FOUND}: {signal}')            
        return signal


    def save_signal(self):
        ''' Save signal Into Database '''
        if self.signal is not None and not self.signal_saved:
            date = datetime.now()
            database = Database(DB_RESYS)
            database.insert_one('signal', {
                'side': self.signal, 
                'date': date,
                'close': self.data.renko.iloc[-1]['close'],
                'test': True
            })
            self.signal_saved = True
            self.log.info(f'Signal {self.signal} Saved {date}')


    def watch_position(self):
        while self.in_position:
            self.log.info(f'{Logger.MONITORING_POSITION} {self.entry_order["orderId"]}')
            sl_status = self.exchange.get_order_status(self.client, self.sl_order, FUTURES)
            self.log.info(f'{Logger.STOP_LOSS_STATUS} {sl_status}')

            # TODO: Calculate distance between current close and entry_price to get PNL
            # _get_current_pnl()
            # PnL = Close Value – Open Value = Contract Quantity x Contract Size x Close Price – Contract Quantity x Contract Size x Open Price
            pnl = self.data.renko.iloc[-1]['close'] - self.entry_price

            if self.exchange.order_status_match_for_stoploss(sl_status):
                self.log.info(Logger.STOP_LOSS_TRIGGERED)                    
                self._clean_up()
                break                
            self.update_sl(self.data.renko.iloc[-1]['close'], self.data.renko.iloc[-3]['DCM_5_5'], BUY if self.signal == SELL else SELL)


    def update_sl(self, close, avg, protection_order_side: str):
        self.log.info(f'{Logger.UPDATING_SL}')        
        distance = get_distance_ptc(self.entry_price, close)
        right_direction = (close < self.entry_price) if (protection_order_side == BUY) else (close > self.entry_price)
        sign = '+' if right_direction else '-'
        self.log.info(f'Distance: {sign}{distance}%')
        if (distance > (self.trailing_ptc * 2)) and right_direction:
            self._increase_trailing_ptc()
            self.sl_price = self._get_stop_loss_price(avg, d=1)
            self.sl_order = self.exchange.update_sl(self.client, self.symbol, self.sl_order, self.sl_price, protection_order_side)
            self.log.info(f'{Logger.SL_UPDATED} {self.sl_order["orderId"]}')
            if self.sl_order is None:
                self._clean_up()


    def open_position(self):
        if self.market == FUTURES and not self.in_position:
            if self.entry_order is None and self.signal is not None:
                self.entry_price = self.data.renko.iloc[-1]['close']
                self.position.symbol = self.symbol
                self.position.market = self.market
                self.position.entry_price = self.entry_price
                self.position.sl_price = self._get_stop_loss_price(self.entry_price, d=5)
                self.position.volume = self.volume
                self.position.leverage = self.leverage
                
                self.entry_order, self.sl_order = self.position.open_with_sl()
                self.transaction.save(self.bot_id, self.symbol, self.market, datetime.now(), self.entry_order['entryPrice'], self.entry_order['orderType'], self.sl_order['side'], self.entry_order['orderQty'], self.sl_order['baseAsset'], self.sl_order['quoteAsset'], self.sl_order['fee'])
                self.in_position = True


    def run(self):
        self.status = self._bot_status()
        while self.status == BotStatus.RUNNING:
            self.status = self._bot_status()
            
            self.data.update_renko_bricks()
            
            self.stochastic.update_stochastic(self.data)
            self.donchian.update_donchian(self.data)
            
            print(f'type: {self.data.renko.iloc[-1][0]} | close: {self.data.renko.iloc[-1][2]} | stoch_K: {self.stochastic.df.iloc[-1][0]} | stoch_D: {self.stochastic.df.iloc[-1][1]} | donchian_M: {self.donchian.df.iloc[-1][1]}')
            self.signal = self.get_signal()
            if self.signal is None:
                continue

            self.save_signal()           
            self.open_position()
            self.watch_position()