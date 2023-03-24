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
        self.bids = self.get_order_book(symbol)['bids']
        return self.bids


    def get_asks(self, symbol: str) -> DataFrame:
        self.asks = self.get_order_book(symbol)['asks']
        return self.asks


    def get_balance(self):
        return float([i for i in self.client.get_account()['balances'] if i['asset'] == 'USDT'][0]['free'])


    def get_order_status(self, order):
        if self.market == SPOT:
            return self.client.get_order(symbol=order['symbol'], orderId=order['orderId'])['status']
        if self.market == FUTURES:
            return self.client.futures_get_order(symbol=order['symbol'], orderId=order['orderId'])['status']


    def update_sl(self, symbol: str, old_stop_order, new_stop_price: float, side: str):
        stop_order = None
        try:
            old_order_status = self.get_order_status(old_stop_order)
            print(f'update_sl: ${old_order_status}')
            if old_order_status == Client.ORDER_STATUS_NEW:
                self.client.futures_cancel_order(symbol=symbol, orderId=old_stop_order['orderId'])
                stop_order = self.client.create_order(symbol=symbol, side=side, sl_price=new_stop_price, with_sl=True)
                # log.info(f"update {symbol} sl {new_stop_price}")
            return stop_order
        except Exception as e:
            # log.error(e)
            return stop_order


    def change_leverage(self, symbol: str, leverage: int):
        return self.client.futures_change_leverage(symbol=symbol, leverage=leverage)


    def create_order(self, symbol: str = None, side: str = None, quantity: float = None, sl_price: float = None, with_sl: bool = False):
        ''' Create an order '''
        if with_sl:
            order = self.client.futures_create_order(
                symbol=symbol,
                side=Client.SIDE_BUY if side == SELL else Client.SIDE_SELL,
                type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
                stopPrice=sl_price,
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


    def order_status_match_for_stoploss(status):
        return status == Client.ORDER_STATUS_FILLED or status == Client.ORDER_STATUS_CANCELED or status == Client.ORDER_STATUS_EXPIRED
