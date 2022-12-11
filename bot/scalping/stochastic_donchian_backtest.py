from core.bot import Bot
from core.exchange import Exchange

class StochasticDonchianBacktest(Bot):

    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        super().__init__(exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid)


    def run(self):
        # self.log.info(f"Bot {self.bot_id} running...")
        print(self.data.renko)