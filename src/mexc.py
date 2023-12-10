"""MEXC tickers parser"""
import httpx
from consts import needle


class MexcClient:
    """HTTP Client to interact with MEXC API"""

    def __init__(self):
        self.client = httpx.Client(http2=True)
        self.headers = {
            "Content-Type": "application/json"
        }

    def get_tickers(self):
        """Returns all tickers list"""
        url = "https://api.mexc.com/api/v3/ticker/bookTicker"
        response = self.client.get(url, headers=self.headers)
        return response.json()

    @staticmethod
    def filter_tickers(tickers):
        """Restructure of list with all tickers"""
        result = {}
        for ticker in tickers:
            # Skip other tickers
            if ticker['symbol'] not in needle:
                continue

            result[ticker['symbol']] = {
                'ask': float(ticker['askPrice']),
                'bid': float(ticker['bidPrice']),
                'ask_size': float(ticker['askQty']),
                'bid_size': float(ticker['bidQty']),
            }

        return result

    def get_data(self):
        """Returns info about all needle tickers"""
        tickers = self.get_tickers()
        data = self.filter_tickers(tickers)
        return data
