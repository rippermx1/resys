from pandas import DataFrame
import pandas_ta as ta
from core.data import Data

class Donchian():

    def __init__(self, data: Data) -> None:
        self.data = data
        self.length = 6
        self.df: DataFrame = self.__get_donchian()
        self.mid_dc_idx = 1



    def __get_donchian(self):
        ''' Get Donchian Channel '''
        return DataFrame(ta.donchian(high=self.data.renko['close'], low=self.data.renko['close'], lower_length=self.length, upper_length=self.length))


    def update_donchian(self, data: Data):
        ''' Update Donchian Channel '''
        self.data = data
        self.df = self.__get_donchian()


    def close_above_mid(self) -> bool:
        ''' Determine if close is above DC '''
        return self.data.renko.iloc[-1]['close'] > self.data.renko.iloc[-1][self.mid_dc_idx]


    def close_below_mid(self) -> bool:
        ''' Determine if close is below DC '''
        return self.data.renko.iloc[-1]['close'] < self.data.renko.iloc[-1][self.mid_dc_idx]

