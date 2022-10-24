from pandas import DataFrame
import numpy as np


# to make sure the new level area does not exist already
def is_far_from_level( value, levels, df: DataFrame):    
    ave =  np.mean(abs(df['open'] - df['close']))    
    return np.sum([abs(value-level)<ave for _,level in levels])==0

# determine bullish fractal 
def is_support( df: DataFrame, i) -> bool:  
    cond1 = df['close'][i] < df['close'][i-1]   
    cond2 = df['close'][i] < df['close'][i+1]   
    cond3 = df['close'][i+1] < df['close'][i+2]   
    cond4 = df['close'][i-1] < df['close'][i-2]  
    return (cond1 and cond2 and cond3 and cond4)

# determine bearish fractal
def is_resistance( df: DataFrame, i) -> bool:  
    cond1 = df['close'][i] > df['close'][i-1]   
    cond2 = df['close'][i] > df['close'][i+1]   
    cond3 = df['close'][i+1] > df['close'][i+2]   
    cond4 = df['close'][i-1] > df['close'][i-2]  
    return (cond1 and cond2 and cond3 and cond4)

#method 1: fractal candlestick pattern
def detect_level_method_1( df: DataFrame):
    shift = 2
    levels = []
    parsed = []
    for i in range(shift, df.shape[0] - shift):
        l = df['close'][i]
        if is_support(df, i):
            if is_far_from_level(l, levels, df):
                levels.append((df.index[i], l))
                parsed.append({
                    'time': df.index[i], 
                    'value': l,
                    'type': 'support'
                    })
        elif is_resistance(df, i):
            if is_far_from_level(l, levels, df):
                levels.append((df.index[i], l))
                parsed.append({
                    'time': df.index[i], 
                    'value': l,
                    'type': 'resistance'
                    })
    return parsed    

#method 2: window shifting method
def detect_level_method_2( df):
    levels = []
    max_list = []
    min_list = []
    parsed = []
    for i in range(5, len(df)-5):
        high_range = df['High'][i-5:i+4]
        current_max = high_range.max()
        if current_max not in max_list:
            max_list = []
        max_list.append(current_max)
        if len(max_list) == 5 and is_far_from_level(current_max, levels, df):
            levels.append((high_range.idxmax(), current_max))
            parsed.append({
                    'time': high_range.idxmax(), 
                    'value': current_max,
                    'type': 'resistance'
                    })
        
        low_range = df['Low'][i-5:i+5]
        current_min = low_range.min()
        if current_min not in min_list:
            min_list = []
        min_list.append(current_min)
        if len(min_list) == 5 and is_far_from_level(current_min, levels, df):
            levels.append((low_range.idxmin(), current_min))
            parsed.append({
                    'time': low_range.idxmin(), 
                    'value': current_min,
                    'type': 'support'
                    })
    return parsed
