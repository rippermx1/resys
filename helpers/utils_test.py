from constants import SPOT
from utils import get_order_book, get_balance
from binance import Client
import os
from dotenv import load_dotenv
from pandas import DataFrame
load_dotenv()

client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_API_SECRET"))

def test_get_order_book():
    df = get_order_book(client, 'BTCUSDT', SPOT)
    
    assert df.shape[0] > 0
    assert df.columns[0] == 'lastUpdateId'
    assert df.columns[1] == 'bids'
    assert df.columns[2] == 'asks'


def test_get_order_book_none():
    df = get_order_book(client, 'BTCUSDT', 'random')

    assert df == None


def test_get_balance():
    assert get_balance(client) > 0


def test_get_balance_return_type():
    assert type(get_balance(client)) == float