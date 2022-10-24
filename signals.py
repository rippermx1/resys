from pandas import DataFrame
import pandas_ta as ta
from dotenv import load_dotenv
import os
import sys
from binance import Client

load_dotenv()

STOCH_LOW = 20
STOCH_HIGH = 80
DELTA = 2

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

def main():
    while True:
        df = DataFrame(client.get_klines(symbol="BTCUSDT", interval=Client.KLINE_INTERVAL_4HOUR, limit=1000))
        print(df.iloc[[0:5]])
        # columns=["time", "open", "high", "low", "close", "volume"]
        df.join(ta.stoch(df["high"], df["low"], df["close"], 14, 3, 6))
        df["ema_fast"] = ta.ema(df["close"], 9)
        df["ema_slow"] = ta.ema(df["close"], 12)
        print(df)

        is_under_stoch_low = df.iloc[-2]["stock_k"] < STOCH_LOW and df.iloc[-2]["stock_d"] < STOCH_LOW
        is_under_delta = df.iloc[-1]["stock_k"] < STOCH_LOW - DELTA and df.iloc[-1]["stock_d"] < STOCH_LOW - DELTA
        is_bearish = (df.iloc[-2]["ema_fast"] < df.iloc[-2]["ema_slow"]) and (df.iloc[-1]["ema_fast"] < df.iloc[-1]["ema_slow"])
        is_close_under_emas = df.iloc[-1]["close"] < df.iloc[-1]["ema_fast"] and df.iloc[-1]["close"] < df.iloc[-1]["ema_slow"]

        if is_under_stoch_low and is_under_delta and is_bearish and is_close_under_emas: 
            print("New candle")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(e)
        main()