"""Live parsing module of OKX market"""
import time
import redis
from mexc import MexcClient
from src.utils import get_timestamp

if __name__ == "__main__":
    # Connection with Redis
    client = redis.Redis(host='localhost', port=6379, db=0)
    # MEXC client
    mexc = MexcClient()

    # Every 3sec updating redis with new tickers
    while True:
        tickers = mexc.get_data()

        if not tickers:
            time.sleep(10)
            continue

        timestamp = get_timestamp()
        print(f"Получены тикеры - {timestamp}")

        for ticker, data in tickers.items():
            # Structure of Redis item
            client.hset(ticker, mapping={
                'ask': data['ask'],
                'bid': data['bid'],
                'ask_size': data['ask_size'],
                'bid_size': data['bid_size'],
            })

        time.sleep(3)
