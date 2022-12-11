from pandas import DataFrame
import pandas_ta as ta
from helpers.constants import STOCHASTIC_OVERBOUGHT, STOCHASTIC_OVERSOLD
from core.data import Data

class Stochastic():

    def __init__(self, data: Data) -> None:
        ''' Initialize Stochastic '''
        self.data = data
        self.k = 14
        self.d = 2
        self.smooth_k = 12
        self.df: DataFrame = self.__get_stochastic()


    def __get_stochastic(self):
        ''' Get Stochastic '''
        return DataFrame(ta.stoch(high=self.data.renko['close'], low=self.data.renko['close'], close=self.data.renko['close'], k=self.k, d=self.d, smooth_k=self.smooth_k))


    def update_stochastic(self, data: Data):
        ''' Update Stochastic '''
        self.data = data
        self.df = self.__get_stochastic()


    def is_overbought(self) -> bool:
        ''' Determine if stochastic is overbought '''
        cond1 = self.df.iloc[-2][0] > STOCHASTIC_OVERBOUGHT and self.df.iloc[-2][1] > STOCHASTIC_OVERBOUGHT
        cond2 = self.df.iloc[-3][0] > STOCHASTIC_OVERBOUGHT and self.df.iloc[-3][1] > STOCHASTIC_OVERBOUGHT
        cond3 = self.df.iloc[-4][0] > STOCHASTIC_OVERBOUGHT and self.df.iloc[-4][1] > STOCHASTIC_OVERBOUGHT
        return cond1 and cond2 and cond3


    def is_oversold(self) -> bool:
        ''' Determine if stochastic is oversold '''
        cond1 = self.df.iloc[-2][0] < STOCHASTIC_OVERSOLD and self.df.iloc[-2][1] < STOCHASTIC_OVERSOLD
        cond2 = self.df.iloc[-3][0] < STOCHASTIC_OVERSOLD and self.df.iloc[-3][1] < STOCHASTIC_OVERSOLD
        cond3 = self.df.iloc[-4][0] < STOCHASTIC_OVERSOLD and self.df.iloc[-4][1] < STOCHASTIC_OVERSOLD
        return cond1 and cond2 and cond3