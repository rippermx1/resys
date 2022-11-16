
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
    date: str = None
    sl_price: float = None
    test: bool = False

    def __init__(self, _side, _date, _sl_price, _test):
        self.side = _side
        self.date = _date
        self.sl_price = _sl_price
        self.test = _test


class Bot:
    pid: int = None
    symbol: str = None
    interval: str = None
    volume: int = None
    leverage: int = None
    brick_size: float = None
    trailing_ptc: float = None


class Permission:
    READ: str = "READ"
    WRITE: str = "WRITE"
    EXEC: str = "EXEC"
    DEL: str = "DEL"

class User:
    id: int = None
    public_key: str = None
    secret_key: str = None
    accept_terms: bool = False
    active: bool = False
    enabled: bool = False
    rut: str = None
    passport: str = None
    email: str = None
    cellphone: str = None
    vip: bool = False
    admin: bool = False
    permission = [Permission.READ, Permission.WRITE, Permission.EXEC, Permission.DEL]
    bots: list = []



