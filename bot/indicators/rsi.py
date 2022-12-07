from pandas import DataFrame
import pandas_ta as ta

class RSI():

    def __init__(self) -> None:
        self.rsi: DataFrame = self._get_rsi()

    def _get_rsi(self, lenght=9):
        ''' Get RSI '''
        return DataFrame(ta.rsi(self.data.renko['close'], lenght))