from sqlalchemy import create_engine, text
from snowflake.sqlalchemy import URL 
from helpers.read_config import read_config

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

    def insert_to_stock_data_table(self, date, stock_symbol, open, high, low, close, volume, local_max):
        with self.connection as connection:
            connection.execute(
                text("""
                    INSERT INTO STOCK_DATA (date, stock_symbol, open, high, low, close, volume, local_max)
                    SELECT :date, :stock_symbol, :open, :high, :low, :close, :volume, :local_max;
                """),
                {
                    "date": date,
                    "stock_symbol": stock_symbol,
                    "open": open,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "local_max": local_max
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

    

test = SnowflakeClient()
test.create_connection()
# test.insert_to_stock_data_table("2000-10-10", "SPY", 10, 10, 10, 10, 10, 10)
# test.clear_table("stock_data")
# test.print_table("stock_data")
test.cleanup()

