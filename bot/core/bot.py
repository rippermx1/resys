from core.exchange import Exchange
from core.transaction import Transaction
from core.data import Data
from models.models import Signal, Position
from core.position import Position as PositionCore
from helpers.logger import Logger
from auth.auth import Auth
from indicators.stochastic import Stochastic
from indicators.donchian import Donchian
from helpers.constants import SELL, DEFAULT_TRAILING_PTC
from helpers.utils import round_down_price


class Bot:

    def __init__(self, exchange: Exchange, symbol, interval, volume, market, leverage, brick_size, trailing_ptc, secret, bot_id, debug, pid):
        self.log = Logger()
        self.transaction = Transaction()
        self.exchange = exchange
        self.position = PositionCore(exchange)
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

        self.client = self.exchange.client
        self.status = self._bot_status()        

        self.data = Data(self.client, self.market, self.symbol, self.interval, self.brick_size)
        
        self.stochastic = Stochastic(self.data)
        self.donchian = Donchian(self.data)

        self._start_bot_info()


    def _start_bot_info(self):
        ''' Print bot info '''
        self.log.info(f"Starting ReSys For: \nSymbol: {self.symbol}\nInterval: {self.interval}\nVolume: {self.volume}\nLeverage: {self.leverage}\nBrick Size: {self.brick_size}\nTrailing Ptc%: {self.trailing_ptc}\nPid: {self.pid}")


    def get_signal(self) -> str:
        pass


    def save_signal(self, signal: Signal):
        pass


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


    def update_sl(self, close, avg, protection_order_side: str):
        pass


    def _get_stop_loss_price(self, price, d):
        ''' Get Stop Loss Price based on Signal Side and apply a Delta (d) Factor Stop Distance '''
        sl_price = (price + self.brick_size * d) if (self.signal == SELL) else (price - self.brick_size * d)
        return round_down_price(self.client, self.symbol, sl_price)

    def watch_position(self):
        pass


    def open_position(self, position: Position):
        pass


    def run(self):
        pass
