class Tier:
    def __init__(self, name, risk, leverage, volume, l_price, s_price):
        self.name = name
        self.risk = risk
        self.leverage = leverage
        self.volume = volume
        self.l_price = l_price
        self.s_price = s_price

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name
