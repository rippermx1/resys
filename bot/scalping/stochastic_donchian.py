from bot import Bot
from exchange import Exchange
from datetime import datetime
from models.models import Position, BotStatus


class StochasticDonchian(Bot):


    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        super().__init__(exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid)


    def get_signal(self) -> str:
        pass


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
            self.signal = self._get_signal()
            if self.signal is None:
                continue

            # self._save_signal(Signal(self.signal, datetime.now(), self.data.renko.iloc[-1]['close'], False))
            self._open_position(Position(self.signal, datetime.now(), self.data.renko.iloc[-1]['close'], False))
            self._watch_position()