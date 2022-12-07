from binance import Client
from pandas import DataFrame
from helpers.constants import SPOT, FUTURES, SELL, BUY


class Exchange:

    def __init__(self, public_key, secret_key, market: str):
        self.name = None
        self.market = market
        self.api_key = public_key
        self.secret_key = secret_key
        self.client = Client(public_key, secret_key)

        self.bids = None
        self.asks = None


    def get_order_book(self, symbol: str) -> DataFrame:
        if self.market == SPOT:
            return DataFrame(self.client.get_order_book(symbol=symbol, limit=10))
        if self.market == FUTURES:
            return DataFrame(self.client.futures_order_book(symbol=symbol, limit=10)).iloc[:, [3, 4]]


    def get_bids(self, symbol: str) -> DataFrame:
        self.bids = self.__get_order_book(symbol)['bids']
        return self.bids


    def get_asks(self, symbol: str) -> DataFrame:
        self.asks = self.__get_order_book(symbol)['asks']
        return self.asks


    def get_balance(self):
        return float([i for i in self.client.get_account()['balances'] if i['asset'] == 'USDT'][0]['free'])


    def get_order_status(self, order):
        if self.market == SPOT:
            return self.client.get_order(symbol=order['symbol'], orderId=order['orderId'])['status']
        if self.market == FUTURES:
            return self.client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])['status']


    def change_leverage(self, symbol: str, leverage: int):
        return self.client.futures_change_leverage(symbol=symbol, leverage=leverage)


    def create_order(self, symbol: str = None, side: str = None, quantity: float = None, price: float = None, with_sl: bool = False):
        ''' Create an order '''
        if with_sl:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_BUY if side == SELL else Client.SIDE_SELL,
                type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
                stopPrice=price,
                closePosition=True
            )
        else:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_SELL if side == SELL else Client.SIDE_BUY,
                type=Client.FUTURE_ORDER_TYPE_MARKET,
                quantity=quantity,
            )
        return order
