from core.exchange import Exchange
from helpers.constants import BUY, SELL, FUTURES
from helpers.utils import round_down, round_down_price
from binance import Client
from pandas import DataFrame

class Position:

    def __init__(self, exchange: Exchange) -> None:
        self.symbol = None
        self.market = None
        self.side = None
        self.entry_price = None
        self.entry_quantity = None
        self.entry_date = None
        self.exit_price = None
        self.exit_quantity = None
        self.exit_date = None
        self.sl_price = None
        self.sl_quantity = None
        self.sl_date = None
        self.tp_price = None
        self.tp_quantity = None
        self.tp_date = None
        self.profit = None
        self.profit_percent = None
        self.leverage = None
        self.status = None
        self.volume = None

        self.exchange = exchange


    def open_with_sl(self):
        self.exchange.change_leverage(self.symbol, self.leverage)
        self.volume = self.volume * self.leverage
        order_book: DataFrame = self.exchange.get_order_book(self.symbol)
        for i in range(len(order_book)):
            level_price = float(order_book.iloc[i].bids[0]) if self.side == SELL else float(order_book.iloc[i].asks[0])
            level_liquidity = float(order_book.iloc[i].bids[1]) if self.side == SELL else float(order_book.iloc[i].asks[1])
            quantity = round(round_down(self.exchange.client, self.symbol, (self.volume / level_price)), 3)
            
            # log.info(f'{Logger.GETTIN_BEST_PRICE}: {level_price}')
            if quantity < level_liquidity:
                entry_order = self.exchange.create_order(
                    symbol=self.symbol, 
                    side=Client.SIDE_SELL if self.side == SELL else Client.SIDE_BUY, 
                    type=Client.FUTURE_ORDER_TYPE_MARKET, 
                    quantity=quantity,
                    with_sl=False
                )
                # log.info(f'{side} Market: {entry_order}')            
                if entry_order is not None:
                    sl_price = round_down_price(self.exchange.client, self.symbol, self.sl_price)
                    stop_order = self.exchange.create_order(
                        symbol=self.symbol,
                        side=Client.SIDE_BUY if self.side == SELL else Client.SIDE_SELL,
                        type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
                        price=sl_price,                    
                        with_sl=True
                    )
                    # log.info(f'{SELL if side == BUY else BUY} Stop {stop_order}')                                              
                break    
        return entry_order, stop_order