import binance
import pandas as pd
from renko import Renko
from pandas import DataFrame
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation

# Initialize Binance client
client = binance.Client()

# Fetch klines data
symbol = 'ETHUSDT'
interval = '1m'

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))


def update_plot(i):
    klines = client.futures_klines(symbol=symbol, interval=interval, limit=1000)

    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time', 'quote_asset_volume', 'num_trades', 'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'])
    df['close'] = df['close'].astype(float)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    renko = Renko(brick_size=3.5,data=df['close'])
    renko.create_renko()
    # renko.check_new_price(df['close'][-1])
    data = renko.bricks
    print(data)

    oc_avg = [(data[i]['open'] + data[i]['close']) / 2 for i in range(len(data))]
    close_prices = [d['close'] for d in data]

    # Calculate the 3-day simple moving average
    sma3 = pd.Series(close_prices).rolling(window=3).mean()
    sma9 = pd.Series(close_prices).rolling(window=9).mean()
    sma30 = pd.Series(close_prices).rolling(window=30).mean()

    # Clear previous plot
    ax.clear()

    ax.plot(oc_avg, label='Open/Close AVG')
    ax.plot(sma3, label='3 fast SMA')
    ax.plot(sma9, label='9 slow SMA')
    ax.plot(sma30, label='30 slow SMA')
    ax.plot(close_prices, label='Close Prices')
    ax.set_title('Closing Prices with a 3-9-30 Simple Moving Average')
    ax.set_xlabel('Time')
    ax.set_ylabel('Price')
    ax.legend()

# Update plot every 10 seconds
ani = FuncAnimation(fig, update_plot, interval=1000)

plt.show()