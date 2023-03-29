from pandas import DataFrame
from binance import AsyncClient, BinanceSocketManager
import asyncio
from tier import Tier

SYMBOL = 'USDCUSDT'
# BUY = 0.998
# SELL = 1.002


async def main():
    # init the client
    client = await AsyncClient.create()
    # init the socket manager
    #bm = BinanceSocketManager(client)
    # start any sockets here, i.e a trade socket
    #ws = bm.kline_futures_socket(symbol=SYMBOL)
    # then start receiving messages
    # async with ws as wscm:
    #    while True:
    #        res = await wscm.recv()
    #        data = DataFrame(res['k'], index=[0])
    #        print(data.iloc[0])
    #        """ if data.iloc[0]['x']:
    #            print('new candle') """

    # await client.close_connection()

    # Tiers are defined as follows:
    tiers = [
        Tier('Tier 5', 0.8, 30, 33.5, 0.9600, 1.040),
        Tier('Tier 4', 1.8, 24, 33.5, 0.9700, 1.030),
        Tier('Tier 3', 2.8, 18, 33.5, 0.9800, 1.020),
        Tier('Tier 2', 3.8, 12, 33.5, 0.9900, 1.010),
        Tier('Tier 1', 4.8, 6, 33.5, 0.9950, 1.005)
    ]

    # Iterate through the tiers and change the leverage
    for tier in tiers:
        await client.futures_change_leverage(
            symbol=SYMBOL, leverage=tier.leverage)
        print(f'Changed leverage to {tier.leverage}x')

        # create a buy limit order for the tier
        buy_order = await client.futures_create_order(
            symbol=SYMBOL,
            side='BUY',
            type='LIMIT',
            timeInForce='GTC',
            quantity=(tier.volume * tier.leverage) / tier.l_price,
            price=tier.l_price
        )
        print(
            f'Created buy order for {tier.volume} at {tier.l_price}',
            buy_order)
        # create a stop loss order for the previous buy order
        stop_loss = await client.futures_create_order(
            symbol=SYMBOL,
            side='SELL',
            type='STOP_MARKET',
            quantity=(tier.volume * tier.leverage) / tier.l_price,
            stopPrice=tier.l_price * tier.risk
        )
        print(
            f'Created stop loss order for {tier.volume} at {tier.l_price}',
            stop_loss)

        # create a sell limit order for the tier
        sell_order = await client.futures_create_order(
            symbol=SYMBOL,
            side='SELL',
            type='LIMIT',
            timeInForce='GTC',
            quantity=(tier.volume * tier.leverage) / tier.s_price,
            price=tier.s_price
        )
        print(
            f'Created sell order for {tier.volume} at {tier.s_price}',
            sell_order)
        # create a stop loss order for the previous sell order
        stop_loss = await client.futures_create_order(
            symbol=SYMBOL,
            side='BUY',
            type='STOP_MARKET',
            quantity=(tier.volume * tier.leverage) / tier.s_price,
            stopPrice=tier.s_price * tier.risk
        )
        print(
            f'Created stop loss order for {tier.volume} at {tier.s_price}',
            stop_loss)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
