from pandas import DataFrame
import pandas_ta as ta
from data import Data

class Indicator:
    def __init__(self, data: Data) -> None:
        self.data = data
        self.donchian: DataFrame = self._get_donchian()
        self.stochastic: DataFrame = self._get_stochastic()
        self.rsi: DataFrame = self._get_rsi()


    def _get_donchian(self, lenght=6):
        ''' Get Donchian Channel '''
        return DataFrame(ta.donchian(high=self.data.renko['close'], low=self.data.renko['close'] ,lower_length=lenght, upper_length=lenght))


    def _get_stochastic(self, k=14, d=2, smooth_k=12):
        ''' Get Stochastic '''
        return DataFrame(ta.stoch(high=self.data.renko['close'], low=self.data.renko['close'] ,close=self.data.renko['close'], k=k, d=d, smooth_k=smooth_k))


    def _get_rsi(self, lenght=9):
        ''' Get RSI '''
        return DataFrame(ta.rsi(self.data.renko['close'], lenght))