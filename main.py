from exchange import Exchange
from bot import Bot
import os
from constants import FUTURES
from logger import Logger
import argparse

log = Logger()
public_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_API_SECRET')

parser = argparse.ArgumentParser()
parser.add_argument('-symbol', '--symbol', type=str, help='Symbol to trade', required=True)
parser.add_argument('-interval', '--interval', type=str, help='Interval', required=True)
parser.add_argument('-volume', '--volume', type=int, help='Volume to trade', required=True)
parser.add_argument('-leverage', '--leverage', type=int, help='Leverage to trade', required=True)
parser.add_argument('-brick_size', '--brick_size', type=float, help='Brick Size in USD', required=True)
parser.add_argument('-trailing_ptc', '--trailing_ptc', type=float, help='Trailing percent', required=True)

args = parser.parse_args()

if __name__ == "__main__":
    pid = os.getpid()
    # TODO: Get public and secret keys from db
    binance = Exchange(public_key, secret_key)
    bot = Bot(binance, args.symbol, args.interval, args.volume, FUTURES, args.leverage, args.brick_size, args.trailing_ptc, debug=False, pid=pid)
    
    log.info(f"Starting ReSys for: {bot.symbol}\nInterval: {bot.interval}\nVolume: {bot.volume}\nLeverage: {bot.leverage}\nBrick Size: {bot.brick_size}\nTrailing Ptc%: {bot.trailing_ptc}\nPid: {pid}")
    # TODO: Control Main Loop by DB
    while True:
        try:
            bot.run()            
        except Exception as e:
            log.error(e)
            print(e)
            continue