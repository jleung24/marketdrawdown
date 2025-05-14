import requests

from helpers.read_config import read_config


config = read_config('AlphaVantage')

url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=SPY&outputsize=full&apikey={config['ApiKey']}"
r = requests.get(url)
data = r.json()

print(data)