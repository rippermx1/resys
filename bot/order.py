from binance import Client
from helpers.constants import SELL, BUY


class Order:

    def __init__(self) -> None:
        self.symbol = None
        self.side = None
        self.price = None
        self.quantity = None
        self.order_type = None
        self.market = None
        self.order = None

    
