from database.db import Database
from helpers.constants import DB_RESYS

class Transaction:

    def __init__(self) -> None:
        self.db = Database(DB_RESYS)

        self.bot_uuid = None
        self.symbol = None
        self.market = None
        self.date = None
        self.price = None
        self.order_type = None
        self.side = None
        self.quantity = None
        self.base_asset = None
        self.quote_asset = None
        self.fee = None

    def save(self, bot_uuid: str, symbol: str, market: str, date, price: float, order_type: str, side: str, quantity: float, base_asset: str, quote_asset: str, fee: float):
        ''' Save a new transaction into DB '''
        return self.db.insert_one('transactions', {
            'bot_uuid': bot_uuid,
            'symbol': symbol,
            'market': market,
            'date': date,
            'price': price,
            'order_type': order_type,
            'side': side,
            'quantity': quantity,
            'base_asset': base_asset,
            'quote_asset': quote_asset,
            'fee': fee
        })

