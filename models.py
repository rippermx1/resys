
class Signal:
    side: str = None
    date: str = None
    close: float = None
    test: bool = False

    def __init__(self, _side, _date, _close, _test):
        self.side = _side
        self.date = _date
        self.close = _close
        self.test = _test


class Position:
    side: str = None
    sl_price: float = None
    entry_date: str = None
    test: bool = False

    def __init__(self, _side, _sl_price, _entry_date, _test):
        self.side = _side
        self.sl_price = _sl_price
        self.entry_date = _entry_date
        self.test = _test