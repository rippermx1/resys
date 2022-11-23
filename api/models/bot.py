from pydantic import BaseModel

class Bot(BaseModel):
    pid: int = None
    symbol: str = None
    interval: str = None
    volume: float = None
    leverage: int = None
    brick_size: float = None
    trailing_ptc: float = None
    active: bool = None
    enabled: bool = None
    status: str = None
    visible: bool = None
    uuid: str = None
    market: str = None


class NewBotRequest(BaseModel):
    secret: str = None
    bot: Bot = None


class UserSecret(BaseModel):
    secret: str = None