from exchange import Exchange
from bot import Bot
import os
from constants import FUTURES
from logger import Logger
from auth import Auth
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('-secret', '--secret', type=str, help='User Secret', required=False)
parser.add_argument('-bot_id', '--bot_id', type=str, help='Bot ID', required=False)
args = parser.parse_args()

log = Logger()
auth = Auth(secret=args.secret)
user_bot = auth.get_bot(args.bot_id)
pid = os.getpid()

if __name__ == "__main__":    
    if not auth._user_exist():
        log.error(f"User not found for secret: {args.secret}")
        os.kill(pid, 9)

    if not auth._user_have_bots():
        log.error(f"User {auth.secret} has no bots created")
        os.kill(pid, 9)

    binance = Exchange(auth.user['public_key'], auth.user['secret_key'])
    bot = Bot(binance, user_bot['symbol'], user_bot['interval'], user_bot['volume'], user_bot['market'], user_bot['leverage'], user_bot['brick_size'], user_bot['trailing_ptc'], debug=False, pid=pid)    
    while user_bot['enable']:
        try:
            auth.update_bot_pid(args.bot_id, pid)
            bot.run()
        except Exception as e:
            log.error(e)
            continue