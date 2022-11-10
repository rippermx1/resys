from asyncio.log import logger
from exchange import Exchange
from bot import ReSys
import os
from constants import FUTURES
from logger import Logger
import argparse

logger = Logger().log
public_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_API_SECRET')
symbol = 'BTCUSDT'
volume = 20
leverage = 50

parser = argparse.ArgumentParser()
parser.add_argument('-symbol', '--symbol', type=str, help='Symbol to trade', required=True)
parser.add_argument('-volume', '--volume', type=int, help='Volume to trade', required=True)
parser.add_argument('-leverage', '--leverage', type=int, help='Leverage to trade', required=True)
parser.add_argument('-brick_size', '--brick_size', type=int, help='Brick Size in USD', required=True)
args = parser.parse_args()

print(args)

if __name__ == "__main__":
    # TODO: Get public and secret keys from db
    binance = Exchange(public_key, secret_key)
    bot = ReSys(binance, args.symbol, args.volume, FUTURES, args.leverage, args.brick_size, debug=False)
    
    logger.info(f"Starting ReSys for: {bot.symbol}\nVolume: {bot.volume}\nLeverage: {bot.leverage}\nBrick Size: {bot.brick_size}")
    print(f"Starting ReSys for: {bot.symbol}\nVolume: {bot.volume}\nLeverage: {bot.leverage}\nBrick Size: {bot.brick_size}")
    while True:
        try:
            bot.run()
            pass
        except Exception as e:
            logger.error(e)
            print(e)
            continue