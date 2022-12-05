from binance import Client
from pandas import DataFrame
from helpers.constants import SPOT, FUTURES
from renko import Renko

class Data:

    def __init__(self, client: Client, market: str, symbol: str, inteval: str, brick_size: float):
        self.client = client
        self.market = market
        self.symbol = symbol
        self.interval = inteval
        self.brick_size = brick_size


    def _get_klines(self, hist: bool = False, start_str: str = None) -> DataFrame:
        ''' Get klines from Binance API '''
        data = None
        if hist and self.market == SPOT:
            data = self.client.get_historical_klines(symbol=self.symbol, interval=self.interval, start_str=start_str, limit=1000)
        else:
            data = self.client.get_klines(symbol=self.symbol, interval=self.interval, limit=1000)
        
        if hist and self.market == FUTURES:
            data = self.client.futures_historical_klines(symbol=self.symbol, interval=self.interval, start_str=start_str, limit=1000)
        else:
            data = self.client.futures_klines(symbol=self.symbol, interval=self.interval, limit=1000)

        data = DataFrame(data)
        data = data.iloc[:,[0,1,2,3,4,5]]
        data.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        data[['open','high','low','close', 'volume']] = data[['open','high','low','close', 'volume']].astype(float) 
        return data


    def _get_renko_bricks(self) -> DataFrame:
        ''' Get Renko bricks '''
        data = self._get_klines()
        renko = Renko(self.brick_size, data['close'])
        renko.create_renko()
        return DataFrame(renko.bricks)