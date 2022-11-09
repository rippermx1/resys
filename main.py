from asyncio.log import logger
from exchange import Exchange
from bot import ReSys
import os
from constants import FUTURES
from logger import Logger

logger = Logger().log
public_key = os.environ.get('BINANCE_API_KEY')
secret_key = os.environ.get('BINANCE_API_SECRET')
symbol = 'BTCUSDT'
volume = 20
leverage = 50

if __name__ == "__main__":
    # TODO: Get public and secret keys from db
    binance = Exchange(public_key, secret_key)
    bot = ReSys(binance, symbol, volume)
    bot.debug = True
    bot.market = FUTURES
    bot.volume = volume
    bot.leverage = leverage
    logger.info(f"Starting ReSys for: {bot.symbol}\nVolume: {bot.volume}\nLeverage: {bot.leverage}")
    print(f"Starting ReSys for: {bot.symbol}\nVolume: {bot.volume}\nLeverage: {bot.leverage}")
    while True:
        try:
            bot.run()
        except Exception as e:
            logger.error(e)
            print(e)
            continue