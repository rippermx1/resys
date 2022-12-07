from indicator import Indicator
from pandas import DataFrame
import pandas_ta as ta

class Donchian(Indicator):

    def __init__(self) -> None:
        self.donchian: DataFrame = self.__get_donchian()
        self.mid_dc_idx = 1


    def __get_donchian(self, lenght=6):
        ''' Get Donchian Channel '''
        return DataFrame(ta.donchian(high=self.data.renko['close'], low=self.data.renko['close'] ,lower_length=lenght, upper_length=lenght))


    def update_donchian(self):
        ''' Update Donchian Channel '''
        self.donchian = self.__get_donchian()


    def close_above_mid(self) -> bool:
        ''' Determine if close is above DC '''
        return self.data.renko.iloc[-1]['close'] > self.data.renko.iloc[-1][self.mid_dc_idx]


    def close_below_mid(self) -> bool:
        ''' Determine if close is below DC '''
        return self.data.renko.iloc[-1]['close'] < self.data.renko.iloc[-1][self.mid_dc_idx]

