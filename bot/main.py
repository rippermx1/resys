from exchange import Exchange
from bot import Bot
import os
from helpers.logger import Logger
from auth.auth import Auth
import argparse
from models import BotStatus

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
    bot = Bot(binance, user_bot['symbol'], user_bot['interval'], user_bot['volume'], user_bot['market'], user_bot['leverage'], user_bot['brick_size'], user_bot['trailing_ptc'], auth.secret, user_bot['uuid'], debug=True, pid=pid)    
    auth.update_bot_pid(args.bot_id, pid)
    while user_bot['enabled']:
        try:
            if user_bot['status'] == BotStatus.STOPPED:
                os.kill(pid, 9)

            if user_bot['status'] == BotStatus.PAUSED:
                print(f'Bot {args.bot_id} {BotStatus.PAUSED}')

            bot.run()
        except Exception as e:
            log.error(e)
            continue