from binance import Client
from helpers.utils import get_window_data, get_avg_extremas, get_maximas, get_minimas, get_maximas_limit, round_down
from helpers.constants import SPOT, FUTURES, BUY, SELL
from models.models import BotStatus
from core.bot import Bot
from core.exchange import Exchange

class Grid(Bot):

    def __init__(self, symbol: str, interval: str, upper_limit: float, lower_limit: float, segment_count: int, order_by_segment: int, volume_per_order: int, stop_treshold: float = 0.0025) -> None:
        self.status = None
        self.symbol = symbol
        self.interval = interval
        self.volume_per_order = volume_per_order
        self.upper_limit = upper_limit
        self.lower_limit = lower_limit
        self.segment_count = segment_count or 3
        self.height = self._get_height() # In PIPs or USD
        self.segment_size = self._get_segment_size()
        self.orders_by_segment = order_by_segment
        self.buy_orders = []
        self.sell_orders = []
        self.stop_orders = []
        self.stop_treshold = stop_treshold
        self.exchange = Exchange('eiaYQ0IImv97voRIaHnoR95C6Ajmj8L23gP636Lzx3pxGWTtF03JPZmTVw8Aq8aS', '0k5CBxnfzjrw5zbiwuni5VqVmT6HLFlwU6gp0ImPgrHsLpfb8NLqSWUw4KNsaPg1', FUTURES)


    def _get_height(self):
        ''' Get the height of the grid '''
        return abs(self.upper_limit - self.lower_limit)


    def _get_segment_size(self):
        ''' Get the segment size of the grid '''
        return self.height / self.segment_count


    def _get_prices_by_zone(self, zone: str):
        ''' Get the lower segment prices '''
        prices = []
        min_size = self.segment_size / self.orders_by_segment
        for i in range(1, self.orders_by_segment + 1):
            prices.append(self.lower_limit + min_size * i if zone is BUY else self.upper_limit - min_size * i)
        return prices


    def get_stop_price(self, zone: str):
        ''' Get the upper stop price '''
        return self.upper_limit + (self.upper_limit * self.stop_treshold) if zone is BUY else self.lower_limit - (self.lower_limit * self.stop_treshold)


    def calculate_total_volume(self):
        ''' Calculate the total volume required '''
        return (self.volume_per_order * self.orders_by_segment) * 2        


    def _detect_zones(self):
        self.interval = Client.KLINE_INTERVAL_5MINUTE
        data = self._get_data()
        data = get_window_data(150, data)#self.window_size
        segment = int(150/4)
        #print(segment)
        a = data.iloc[-segment*4:-segment*3]
        b = data.iloc[-segment*3:-segment*2]
        c = data.iloc[-segment*2:-segment]
        d = data.iloc[-segment:]
        
        [max_a, min_a] = get_maximas(a), get_minimas(a)
        [max_b, min_b] = get_maximas(b), get_minimas(b)
        [max_c, min_c] = get_maximas(c), get_minimas(c)
        [max_d, min_d] = get_maximas(d), get_minimas(d)

        sell_zone = get_maximas_limit(get_avg_extremas(max_a, max_b, max_c, max_d), 1)
        buy_zone  = get_maximas_limit(get_avg_extremas(min_a, min_b, min_c, min_d), 1)
        print(sell_zone, buy_zone)
        return [sell_zone, buy_zone]


    async def run(self):
        while self.status == BotStatus.RUNNING:
            # self._detect_zones()
            pass



if __name__ == '__main__':
    grid = Grid('BTCUSDT', Client.KLINE_INTERVAL_5MINUTE, 17600, 15700, 3, 5, 5, 0.01)
    print(f'Total Volume Required: {grid.calculate_total_volume()}')

    for buy_price in grid._get_prices_by_zone(BUY):
        print(f'BUY Price: {buy_price}')
        print(f'BUY Stop Price: {grid.get_stop_price(BUY)}')
        # create a stop-market buy order on futures
        order = grid.exchange.client.futures_create_order(
            symbol=grid.symbol,
            side=Client.SIDE_BUY,
            type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
            quantity = round(round_down(grid.exchange.client, grid.symbol, (grid.volume / buy_price)), 3),
            price=buy_price,
            stopPrice=grid.get_stop_price(BUY),
            timeInForce=Client.TIME_IN_FORCE_GTC
        )
    for sell_price in grid._get_prices_by_zone(SELL):
        print(f'SELL Price: {sell_price}')
        print(f'SELL Stop Price: {grid.get_stop_price(SELL)}')
        # create a stop-market buy order on futures
        order = grid.exchange.client.futures_create_order(
            symbol=grid.symbol,
            side=Client.SIDE_SELL,
            type=Client.FUTURE_ORDER_TYPE_STOP_MARKET,
            quantity = round(round_down(grid.exchange.client, grid.symbol, (grid.volume / sell_price)), 3),
            price=sell_price,
            stopPrice=grid.get_stop_price(SELL),
            timeInForce=Client.TIME_IN_FORCE_GTC
        )

    print(f'Grid Height: {grid.height}')
    print(f'Grid Segment Size: {grid.segment_size}')