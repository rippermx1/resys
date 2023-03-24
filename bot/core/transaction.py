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

    def save(self):
        ''' Save a new transaction into DB '''
        return self.db.insert_one('transactions', {
            'bot_uuid': self.bot_uuid,
            'symbol': self.symbol,
            'market': self.market,
            'date': self.date,
            'price': self.price,
            'order_type': self.order_type,
            'side': self.side,
            'quantity': self.quantity,
            'base_asset': self.base_asset,
            'quote_asset': self.quote_asset,
            'fee': self.fee
        })

