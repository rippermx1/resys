import math
from pandas import DataFrame
from binance import AsyncClient, BinanceSocketManager
from binance.exceptions import BinanceAPIException, BinanceOrderException
import asyncio
from tier import Tier
from dotenv import load_dotenv
import os
load_dotenv()

SYMBOL = 'USDCUSDT'

# Tiers are defined as follows:
tiers = [
    Tier('Tier 5', 0.008, 30, 20, 0.9600, 1.040),
]
""" Tier('Tier 4', 1.8, 24, 20, 0.9700, 1.030),
    Tier('Tier 3', 2.8, 18, 20, 0.9800, 1.020),
    Tier('Tier 2', 3.8, 12, 20, 0.9900, 1.010),
    Tier('Tier 1', 4.8, 6, 20, 0.9950, 1.005) """
# List of orders
orders = []


async def main():
    try:
        # init the client
        client = await AsyncClient.create(
            api_key=os.getenv('BINANCE_API_KEY'),
            api_secret=os.getenv('BINANCE_API_SECRET'))

        # Iterate through the tiers and change the leverage
        for tier in tiers:
            print(f'Working on {tier.name}...')

            long, sl_long = None, None
            short, sl_short = None, None

            # Change leverage to the tier's leverage
            await change_leverage(tier, client)

            # Create a new order LONG for the tier
            long, sl_long = await new_order(tier, SYMBOL, 'BUY',
                                            'LIMIT', True, client)

            # Create a new order SHORT for the tier
            """ short, sl_short = await new_order(tier, SYMBOL, 'SELL',
                                              'LIMIT', True, client) """

            # Add the orders to the list
            await add_order(tier, long, sl_long, short, sl_short)
    except BinanceAPIException as e:
        print(e.message)
        return


async def change_leverage(tier: Tier, client: AsyncClient = None):
    '''
    Change the leverage to the tier's leverage
    '''
    try:
        await client.futures_change_leverage(
            symbol=SYMBOL, leverage=tier.leverage)
        print(f'Changed leverage to {tier.leverage}x')
    except BinanceAPIException as e:
        print(e.message)
        return


async def add_order(tier: Tier, long, sl_long, short, sl_short):
    '''
    Add the order to the list of orders
    '''
    orders.append({
        'tier': tier.name,
        'long': {
            'order': long,
            'stop_loss': sl_long
        },
        'short': {
            'order': short,
            'stop_loss': sl_short
        }})
    print(f'Added order for {tier.name}')
    print(DataFrame(orders))


async def new_order(tier: Tier, symbol: str, side: str, type: str,
                    with_stop_loss: bool = True, client: AsyncClient = None):
    '''
    Create a new order for the tier
    Given the side (BUY or SELL), and the type (LIMIT or MARKET)
    '''
    order = None
    sl_order = None
    try:
        qty_rounded = await get_quantity_rounded(client, symbol, tier, side)
        tier_price = get_price(side, tier)

        # create an order for the tier
        order = await client.futures_create_order(
            symbol=symbol,
            side='SELL' if (side == 'SELL') else 'BUY',
            type=type,
            timeInForce='GTC',
            quantity=qty_rounded,
            price=tier_price,
        )
        print(
            f'Created {side} order for {tier.name} at {tier_price} \
            with {qty_rounded}USDT', order)
        if with_stop_loss:
            # create a stop loss order for the previous sell order
            sl_order = await client.futures_create_order(
                symbol=SYMBOL,
                side='BUY' if (side == 'SELL') else 'SELL',
                type='STOP_MARKET',
                quantity=qty_rounded,
                stopPrice=await get_stop_price_rounded(client, symbol,
                                                       tier, side)
            )
            print(
                f'Created {side} order for {tier.name} at {tier_price} \
                with {qty_rounded}USDT', sl_order)
    except Exception as e:
        print(e)
        return None, None
    return order, sl_order


async def get_stop_price_rounded(client: AsyncClient, symbol,
                                 tier: Tier, side: str):
    ''' Get the stop price rounded to the correct step size '''
    return await round_down_price(client, symbol, get_stop_price(side, tier))


def get_stop_price(side: str, tier: Tier):
    '''
    Get the stop price for the given tier (price - (price * risk))
    '''
    return tier.s_price + (tier.s_price * tier.risk) if (side == 'SELL') else \
        tier.l_price - (tier.l_price * tier.risk)


def get_quantity(tier: Tier):
    '''
    Get the quantity for the given tier (volume * leverage)
    '''
    return tier.volume * tier.leverage


def get_price(side: str, tier: Tier):
    '''
    Get the price of Tier for the given Side (Long or Short)
    '''
    return tier.s_price if (side == 'SELL') else tier.l_price


async def round_down(client: AsyncClient, symbol, number):
    info = await client.get_symbol_info(symbol=symbol)
    step_size = [float(f['stepSize']) for f in info['filters']
                 if f['filterType'] == 'LOT_SIZE'][0]
    step_size = '%.8f' % step_size
    step_size = step_size.rstrip('0')
    decimals = len(step_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


async def round_down_price(client: AsyncClient, symbol, number):
    info = await client.get_symbol_info(symbol=symbol)
    tick_size = [float(f['tickSize']) for f in info['filters']
                 if f['filterType'] == 'PRICE_FILTER'][0]
    tick_size = '%.8f' % tick_size
    tick_size = tick_size.rstrip('0')
    decimals = len(tick_size.split('.')[1])
    return math.floor(number * 10 ** decimals) / 10 ** decimals


async def get_quantity_rounded(client: AsyncClient, symbol: str,
                               tier: Tier, side: str):
    '''
    Get the quantity rounded for the given tier (volume * leverage) / price
    '''
    return await round_down(client, symbol,
                            get_quantity(tier) / get_price(side, tier))


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
