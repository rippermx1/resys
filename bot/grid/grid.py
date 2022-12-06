from binance import Client
from helpers.utils import get_window_data, get_avg_extremas, get_maximas, get_minimas, get_maximas_limit

class Grid:

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