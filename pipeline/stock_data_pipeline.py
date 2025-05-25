from database.pydantic_models import *
from database.rds_client import RdsClient
from alpha_vantage.alpha_vantage_client import AlphaVantageClient


class StockDataPipeline():

    def __init__(self, client: str):
        self.alpha_vantage = AlphaVantageClient()

        self.client = RdsClient()
        
        self.client.create_engine()
        self.stock_data = None
        self.split_data = None

    def update_database(self, stock_symbol: str):
        self.stock_data = self.alpha_vantage.get_data(stock_symbol)
        self.split_data =self.alpha_vantage.get_splits(stock_symbol)

        if self.split_data['data'] != []:
            self.insert_split_data(stock_symbol)
        
        self.insert_stock_data(stock_symbol)
        
        self.client.cleanup()

    def insert_split_data(self, stock_symbol: str):
        for data in self.split_data['data']:
            data_dict = {}

            if self.client.split_data_exists(stock_symbol, data['effective_date']):
                continue

            data_dict = {
                'date': data['effective_date'],
                'stock_symbol': stock_symbol,
                'split_factor': data['split_factor']
            }

            if pydantic_data := SplitData(**data_dict):
                self.client.insert_to_split_data_table(pydantic_data)

    def insert_stock_data(self, stock_symbol: str):
        first = True

        for date, data in reversed(self.stock_data['Time Series (Daily)'].items()):
            data_dict = {}      
            stock_data_id = f"{date.replace('-', '')}_{stock_symbol}"

            if self.client.stock_data_id_exists(stock_data_id):
                continue
            
            split_factor = float(self.client.get_split_factor(stock_symbol, date))
            
            data_dict = {
                'stock_data_id': stock_data_id,
                'date': date,
                'stock_symbol': stock_symbol,
                'open': float(data['1. open']) * split_factor,
                'high': float(data['2. high']) * split_factor,
                'low': float(data['3. low']) * split_factor,
                'close': float(data['4. close']) * split_factor,
                'volume': float(data['5. volume'])
            }
            
            if self.client.no_stock_data(stock_symbol) and first:
                data_dict['local_max_id'] = stock_data_id
            else:
                data_dict['local_max_id'] = self.get_local_max_id(data_dict)
            
            if pydantic_data := StockData(**data_dict):
                self.client.insert_to_stock_data_table(pydantic_data)
            
            first = False

    def get_local_max_id(self, data_dict: dict):
        prev_max_id = self.client.get_previous_max(data_dict['date'], data_dict['stock_symbol'])
        prev_max_data = self.client.get_stock_data(prev_max_id)
        prev_max = float(prev_max_data[4])
        if prev_max > data_dict['high']:
            return prev_max_id
        
        return data_dict['stock_data_id']


if __name__ == "__main__":
    pipeline = StockDataPipeline("rds")
    pipeline.update_database("QQQ")
