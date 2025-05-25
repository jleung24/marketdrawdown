import requests
import json

from helpers.read_config import read_config


config = read_config('AlphaVantage')


class AlphaVantageClient:

    def __init__(self):
        self.api_key = config['ApiKey']
        self.data = None

    def get_data(self, stock_symbol: str) -> dict:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={stock_symbol}&outputsize=full&apikey={self.api_key}"
        self.data = requests.get(url).json()

        return self.data

    def get_splits(self, stock_symbol: str) -> dict:
        url = f"https://www.alphavantage.co/query?function=SPLITS&symbol={stock_symbol}&apikey={self.api_key}"
        self.data = requests.get(url).json()

        return self.data

    def write_data_to_file(self):
        if self.data:
            with open('data.json', 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
