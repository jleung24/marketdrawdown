from sqlalchemy import create_engine, text
from snowflake.sqlalchemy import URL 

from helpers.read_config import read_config
from snowflake.pydantic_models import *


config = read_config('Snowflake')


class SnowflakeClient:

    def __init__(self):
        self.connection = None
        self.engine = None

    def create_connection(self):
        self.engine = create_engine(
            URL(
                account = config['AccountIdentifier'],
                user = config['User'],
                password = config['Password'],
                database = 'marketdata',
                schema = 'public',
                warehouse = 'compute_wh',
                role='accountadmin',
            )
        )

        self.connection = self.engine.connect()

    def cleanup(self):
        self.connection.close()
        self.engine.dispose()

    def insert_to_stock_data_table(self,stock_data: StockData):
        with self.connection as connection:
            connection.execute(
                text("""
                    INSERT INTO STOCK_DATA (stock_data_id, date, stock_symbol, open, high, low, close, volume, local_max_id)
                    SELECT :stock_data_id, :date, :stock_symbol, :open, :high, :low, :close, :volume, :local_max_id;
                """),
                {
                    "stock_data_id": stock_data.stock_data_id,
                    "date": stock_data.date,
                    "stock_symbol": stock_data.stock_symbol,
                    "open": stock_data.open,
                    "high": stock_data.high,
                    "low": stock_data.low,
                    "close": stock_data.close,
                    "volume": stock_data.volume,
                    "local_max_id": stock_data.local_max_id
                }
            )
            connection.commit()
    
    def clear_table(self, table_name):
        with self.connection as connection:
            statement = text(f"DELETE FROM {table_name};")
            connection.execute(statement)
            connection.commit()

    def print_table(self, table_name):
        with self.connection as connection:
            statement = text(f"SELECT * FROM {table_name}")
            for row in connection.execute(statement):
                print(row)

    

# test = SnowflakeClient()
# test.create_connection()

# # data = {
# #     "stock_data_id": "20001010_SPY",
# #     "date": "2000-10-10",
# #     "stock_symbol": "SPY",
# #     "open": 10,
# #     "high": 10,
# #     "low": 10,
# #     "close": 10,
# #     "volume": 10,
# #     "local_max_id": "20001010_SPY"
# # }

# # if stock_data := StockData(**data):
# #     pass

# # test.insert_to_stock_data_table(stock_data)
# # test.insert_to_stock_data_table("20001010_SPY","2000-10-10", "SPY", 10, 10, 10, 10, 10, "20001010_SPY")
# test.clear_table("stock_data")
# # test.print_table("stock_data")
# test.cleanup()

