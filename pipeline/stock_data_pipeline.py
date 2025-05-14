from snowflake.pydantic_models import *
from snowflake.snowflake_client import SnowflakeClient
from alpha_vantage.alpha_vantage_client import AlphaVantageClient


class StockDataPipeline():

    def __init__(self):
        self.alpha_vantage = AlphaVantageClient()
        self.snowflake = SnowflakeClient()
        self.snowflake.create_engine()
        self.stock_data = None

    def update_database(self, stock_symbol: str):
        self.stock_data = self.alpha_vantage.get_data(stock_symbol)
        data_dict = {}

        for date, data in reversed(self.stock_data['Time Series (Daily)'].items()):           
            stock_data_id = f"{date.replace("-", "")}_{stock_symbol}"

            if self.snowflake.stock_data_id_exists(stock_data_id):
                continue

            data_dict['stock_data_id'] = stock_data_id
            data_dict['date'] = date
            data_dict['stock_symbol'] = stock_symbol
            data_dict['open'] = float(data['1. open'])
            data_dict['high'] = float(data['2. high'])
            data_dict['low'] = float(data['3. low'])
            data_dict['close'] = float(data['4. close'])
            data_dict['volume'] = float(data['5. volume'])
            
            if self.snowflake.no_stock_data(stock_symbol):
                data_dict['local_max_id'] = stock_data_id
            else:
                data_dict['local_max_id'] = self.get_local_max_id(data_dict)
            
            if pydantic_data := StockData(**data_dict):
                pass

            self.snowflake.insert_to_stock_data_table(pydantic_data)
        
        self.snowflake.cleanup()

    def get_local_max_id(self, data_dict: dict):
        prev_max_id = self.snowflake.get_previous_max(data_dict['date'], data_dict['stock_symbol'])
        prev_max_data = self.snowflake.get_stock_data(prev_max_id)
        prev_max = float(prev_max_data[4])

        if prev_max > data_dict['high']:
            return prev_max_id
        
        return data_dict['stock_data_id']

if __name__ == "__main__":
    pipeline = StockDataPipeline()
    pipeline.update_database("SPY")
