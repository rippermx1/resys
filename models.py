
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
