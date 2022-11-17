from exchange import Exchange
from bot import Bot
import os
from constants import FUTURES
from logger import Logger
from auth import Auth
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-secret', '--secret', type=str, help='User Secret', required=False)
parser.add_argument('-symbol', '--symbol', type=str, help='Symbol to trade', required=False)
parser.add_argument('-interval', '--interval', type=str, help='Interval', required=False)
parser.add_argument('-volume', '--volume', type=int, help='Volume to trade', required=False)
parser.add_argument('-leverage', '--leverage', type=int, help='Leverage to trade', required=False)
parser.add_argument('-brick_size', '--brick_size', type=float, help='Brick Size in USD', required=False)
parser.add_argument('-trailing_ptc', '--trailing_ptc', type=float, help='Trailing percent', required=False)

args = parser.parse_args()

log = Logger()
auth = Auth(secret=args.secret)
pid = os.getpid()

if __name__ == "__main__":    
    if auth._user_exist():
        public_key, secret_key = auth.user['public_key'], auth.user['secret_key']
        binance = Exchange(public_key, secret_key)
        if auth._user_have_bots():
            print('You already have a bot running', auth.user['bots'][0])
            bot = Bot(binance, auth.user['bots'][0]['symbol'], auth.user['bots'][0]['interval'], auth.user['bots'][0]['volume'], FUTURES, auth.user['bots'][0]['leverage'], auth.user['bots'][0]['brick_size'], auth.user['bots'][0]['trailing_ptc'], debug=False, pid=pid)
    else:
        # NOTE: This is only a backdoor for manual use
        log.error(f"User not found for secret: {args.secret}")
        binance = Exchange(os.environ.get('BINANCE_API_KEY'), os.environ.get('BINANCE_API_SECRET'))
        bot = Bot(binance, args.symbol, args.interval, args.volume, FUTURES, args.leverage, args.brick_size, args.trailing_ptc, debug=True, pid=pid)
    
    log.info(f"Starting ReSys For: \nSymbol: {bot.symbol}\nInterval: {bot.interval}\nVolume: {bot.volume}\nLeverage: {bot.leverage}\nBrick Size: {bot.brick_size}\nTrailing Ptc%: {bot.trailing_ptc}\nPid: {pid}")
    # TODO: Control Main Loop by DB
    while True:
        try:
            bot.run()                    
        except Exception as e:
            log.error(e)
            print(e)
            continue