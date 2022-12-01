from binance import Client

class Exchange:
    name = None
    client = None
    market = None
    api_key = None
    api_secret = None

    def __init__(self, public_key, secret_key):
        self.api_key = public_key
        self.secret_key = secret_key
        self.client = Client(public_key, secret_key)

    def get_client(self):
        return self.client
