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



def backtest(df: DataFrame, lookback: int = 15):
    ''' Backtest '''
    in_short_position = False
    in_long_position = False
    signal = None
    win, loss = 0, 0
    for i in range(lookback, len(df)):
        # print(df.iloc[i])
        is_turning_down = df.iloc[i]['type'] == DOWN and df.iloc[i-1]['type'] == UP and df.iloc[i-2]['type'] == UP and df.iloc[i-3]['type'] == UP
        is_turning_up = df.iloc[i]['type'] == UP and df.iloc[i-1]['type'] == DOWN and df.iloc[i-2]['type'] == DOWN and df.iloc[i-3]['type'] == DOWN

        s1 = df.iloc[i]['STOCHk_14_2_4'] < df.iloc[i]['STOCHd_14_2_4']
        s2 = df.iloc[i-1]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-1]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s3 = df.iloc[i-2]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-2]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        s4 = df.iloc[i-3]['STOCHk_14_2_4'] > STOCH_OVERBOUGHT and df.iloc[i-3]['STOCHd_14_2_4'] > STOCH_OVERBOUGHT
        is_overbought = s1 and s2 and s3 and s4

        close_above_dc = df.iloc[i]['close'] > df.iloc[i]['DCM_5_5']
        close_under_dc = df.iloc[i]['close'] < df.iloc[i]['DCM_5_5']
        
        b1 = df.iloc[i]['STOCHk_14_2_4'] > df.iloc[i]['STOCHd_14_2_4']
        b2 = df.iloc[i-1]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-1]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b3 = df.iloc[i-2]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-2]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        b4 = df.iloc[i-3]['STOCHk_14_2_4'] < STOCH_OVERSOLD and df.iloc[-3]['STOCHd_14_2_4'] < STOCH_OVERSOLD
        is_oversold = b1 and b2 and b3 and b4

        if is_turning_down and is_overbought and close_under_dc and not in_short_position:
            in_short_position = True
            in_long_position = False
            
            signal = {
                'side': 'SELL',
                'entry_price': df.iloc[i]['close'],
                'sl': df.iloc[i-1]['close'] + 20,
                'tp': df.iloc[i-1]['close'] - 80,
            }
            print(f'SELL {signal}')
                
        if is_turning_up and is_oversold and close_above_dc and not in_long_position:
            in_short_position = False
            in_long_position = True
            
            signal = {
                'side': 'BUY',
                'entry_price': df.iloc[i]['close'],
                'sl': df.iloc[i-1]['close'] - 20,
                'tp': df.iloc[i-1]['close'] + 80,
            }
            print(f'BUY {signal}')

        if in_short_position:
            if df.iloc[i]['close'] >= signal['sl']:
                in_short_position = False
                loss += 1
                print(f'STOP {df.iloc[i].close}')                            
                
            elif df.iloc[i]['close'] <= signal['tp']:
                in_short_position = False
                win += 1
                print(f'PROFIT {df.iloc[i].close}')   
        if in_long_position:
            if df.iloc[i]['close'] <= signal['sl']:
                in_short_position = False
                loss += 1
                print(f'STOP {df.iloc[i].close}')                            
                
            elif df.iloc[i]['close'] >= signal['tp']:
                in_short_position = False
                win += 1
                print(f'PROFIT {df.iloc[i].close}')                            
    print(f'win: {win} | loss: {loss}')