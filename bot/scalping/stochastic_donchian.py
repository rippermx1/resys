from core.bot import Bot
from core.exchange import Exchange
from datetime import datetime
from models.models import Position, BotStatus
from helpers.logger import Logger
from helpers.constants import BUY, SELL


class StochasticDonchian(Bot):


    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        super().__init__(exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid)


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


    def _watch_position(self):
        return super()._watch_position()


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
            
            self._open_position(Position(self.signal, datetime.now(), self.data.renko.iloc[-1]['close'], False))
            self._watch_position()