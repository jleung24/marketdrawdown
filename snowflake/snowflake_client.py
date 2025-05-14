from sqlalchemy import create_engine, text
from snowflake.sqlalchemy import URL 

from helpers.read_config import read_config
from snowflake.pydantic_models import *


config = read_config('Snowflake')


class SnowflakeClient:

    def __init__(self):
        self.engine = None

    def create_engine(self):
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

    def cleanup(self):
        self.engine.dispose()

    def insert_to_stock_data_table(self,stock_data: StockData):
        with self.engine.connect() as connection:
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
    
    def clear_table(self, table_name: str):
        with self.engine.connect() as connection:
            statement = text(f"DELETE FROM {table_name};")
            connection.execute(statement)
            connection.commit()

    def print_table(self, table_name: str):
        with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM {table_name}")
            for row in connection.execute(statement):
                print(row)

    def stock_data_id_exists(self, stock_data_id: str) -> bool:
         with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM stock_data WHERE stock_data_id = '{stock_data_id}'")
            for row in connection.execute(statement):
                return True
                
            return False
    
    def table_is_empty(self, table_name: str):
         with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM {table_name}")
            for row in connection.execute(statement):
                return False
                
            return True
         
    def no_stock_data(self, stock_symbol: str):
         with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM stock_data WHERE stock_symbol = '{stock_symbol}'")
            for row in connection.execute(statement):
                return False
                
            return True
         
    def get_previous_max(self, date: str, stock_symbol: str) -> str:
        with self.engine.connect() as connection:
            statement = text(f"""SELECT local_max_id FROM stock_data WHERE stock_symbol = '{stock_symbol}' AND date in 
                                (
                                    SELECT MAX(date) FROM stock_data WHERE stock_symbol = '{stock_symbol}' AND date < TO_DATE('{date}')
                                )
                            """)
            for row in connection.execute(statement):
                return row[0]

    def get_stock_data(self, stock_data_id: str):
        with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM stock_data WHERE stock_data_id = '{stock_data_id}'")
            for row in connection.execute(statement):
                return row
