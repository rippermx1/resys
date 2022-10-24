from pandas import DataFrame
import numpy as np


def get_signals(df: DataFrame):
    signals = []
    
    for i in range(5, len(df)):
        is_bullish = (df['close'][i-1] > df['close'][i-2]) and (df['close'][i-2] > df['close'][i-3]) and (df['close'][i-3] > df['close'][i-4])
        is_bearish = (df['close'][i-1] < df['close'][i-2]) and (df['close'][i-2] < df['close'][i-3]) and (df['close'][i-3] < df['close'][i-4])
        is_turning_down = (df['close'][i] < df['close'][i-1])
        is_turning_up = (df['close'][i] > df['close'][i-1])
        is_overbought = (df['STOCHk_14_2_4'][i] < df['STOCHd_14_2_4'][i]) and (df['STOCHk_14_2_4'][i-1] > 95 and df['STOCHd_14_2_4'][i-1] > 95) and (df['STOCHk_14_2_4'][i-2] > 95 and df['STOCHd_14_2_4'][i-2] > 95) and (df['STOCHk_14_2_4'][i-3] > 95 and df['STOCHd_14_2_4'][i-3] > 95)
        is_oversold   = (df['STOCHk_14_2_4'][i] > df['STOCHd_14_2_4'][i]) and (df['STOCHk_14_2_4'][i-1] < 5 and df['STOCHd_14_2_4'][i-1] < 5) and (df['STOCHk_14_2_4'][i-2] < 5 and df['STOCHd_14_2_4'][i-2] < 5) and (df['STOCHk_14_2_4'][i-3] < 5 and df['STOCHd_14_2_4'][i-3] < 5)
        if is_bullish and is_turning_down and is_overbought:
            signals.append({
                'time': df.index[i],
                'value': df['close'][i],
                'type': 'sell'
            })
        elif is_bearish and is_turning_up and is_oversold:
            signals.append({
                'time': df.index[i],
                'value': df['close'][i],
                'type': 'buy'
            })
    return signals