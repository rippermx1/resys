from bot import _is_overbought, _is_oversold, _is_turning_down, _is_turning_up, _get_signal, _close_above_dc, _close_below_dc
from pandas import DataFrame

from constants import BUY, SELL

def test_is_overbought():
    df = DataFrame({
            "STOCHk_14_2_4": [96, 98, 100, 95],            
            "STOCHd_14_2_4": [96, 98, 100, 97],
        })
    assert _is_overbought(df) == True


def test_is_not_overbought():
    df = DataFrame({
            "STOCHk_14_2_4": [88, 92, 100, 95],            
            "STOCHd_14_2_4": [88, 92, 100, 97],
        })
    assert _is_overbought(df) == False


def test_is_oversold():
    df = DataFrame({
            "STOCHk_14_2_4": [0, 0, 4, 7],            
            "STOCHd_14_2_4": [0, 0, 4, 5],
        })
    assert _is_oversold(df) == True


def test_is_not_oversold():
    df = DataFrame({
            "STOCHk_14_2_4": [7, 2, 0, 7],            
            "STOCHd_14_2_4": [7, 2, 0, 5],
        })
    assert _is_oversold(df) == False


def test_is_turning_down():
    df = DataFrame({ "type": ['up', 'up', 'up', 'down'] })
    assert _is_turning_down(df) == True


def test_is_not_turning_down():
    df = DataFrame({ "type": ['down', 'up', 'up', 'down'] })
    assert _is_turning_down(df) == False


def test_is_turning_up():
    df = DataFrame({ "type": ['down', 'down', 'down', 'up'] })
    assert _is_turning_up(df) == True


def test_is_not_turning_up():
    df = DataFrame({ "type": ['up', 'down', 'down', 'up'] })
    assert _is_turning_up(df) == False


def test_get_signal_buy():
    df = DataFrame({
            "STOCHk_14_2_4": [4, 2, 0, 7],            
            "STOCHd_14_2_4": [4, 2, 0, 5],
            "type": ['down', 'down', 'down', 'up']
        })
    assert _get_signal(df) == BUY


def test_get_signal_sell():
    df = DataFrame({
            "STOCHk_14_2_4": [96, 98, 100, 94],            
            "STOCHd_14_2_4": [96, 98, 100, 96],
            "type": ['up', 'up', 'up', 'down']
        })
    assert _get_signal(df) == SELL


def test_get_signal_none():
    df = DataFrame({
            "STOCHk_14_2_4": [5, 98, 100, 94],            
            "STOCHd_14_2_4": [96, 98, 100, 5],
            "type": ['up', 'up', 'up', 'down']
        })
    assert _get_signal(df) == None


def test_close_above_dc():
    df = DataFrame({
            "close": [100, 101, 102, 103],
            "DCM_5_5": [100, 100, 100, 100]
        })
    assert _close_above_dc(df) == True


def test_not_close_above_dc():
    df = DataFrame({
            "close": [95, 99, 100, 95],
            "DCM_5_5": [100, 100, 100, 100]
        })
    assert _close_above_dc(df) == False


def test_close_below_dc():
    df = DataFrame({
            "close": [100, 98, 95, 90],
            "DCM_5_5": [100, 100, 100, 100]
        })
    assert _close_below_dc(df) == True


def test_not_close_below_dc():
    df = DataFrame({
            "close": [95, 99, 96, 103],
            "DCM_5_5": [100, 100, 100, 100]
        })
    assert _close_below_dc(df) == False