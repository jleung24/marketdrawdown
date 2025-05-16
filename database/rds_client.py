from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

from helpers.read_config import read_config
from database.pydantic_models import *
from computation.drawdown import Drawdown


config = read_config('RDS')


class RdsClient:

    def __init__(self):
        self.engine = None
        self.stock_data_id_list = []

    def create_engine(self):
        url = URL.create(
            drivername="postgresql+psycopg2",
            username=config['User'],
            password=config['Password'],
            host=config['Host'],
            port=config['Port'],
            database='market_data'
        )
        self.engine = create_engine(url)

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
        if not self.stock_data_id_list:
            self.cache_stock_data_ids()
        
        if stock_data_id in self.stock_data_id_list:
            return True

        return False
    
    def cache_stock_data_ids(self):
        self.stock_data_id_list = []
        with self.engine.connect() as connection:
            statement = text(f"SELECT stock_data_id FROM stock_data")
            for row in connection.execute(statement):
                self.stock_data_id_list.append(row[0])
    
    def table_is_empty(self, table_name: str):
        with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM {table_name}")
            for row in connection.execute(statement):
                return False
                
            return True
         
    def no_stock_data(self, stock_symbol: str):
        if not self.stock_data_id_list:
            self.cache_stock_data_ids()

        if any(stock_symbol in id for id in self.stock_data_id_list):
            return False    
        
        return True
         
    def get_previous_max(self, date: str, stock_symbol: str) -> str:
        with self.engine.connect() as connection:
            statement = text(f"""
                SELECT local_max_id FROM stock_data WHERE stock_symbol = '{stock_symbol}' AND date in 
                    (
                        SELECT MAX(date) FROM stock_data WHERE stock_symbol = '{stock_symbol}' AND date < TO_DATE('{date}', 'YYYY-MM-DD')
                    )
            """)
            for row in connection.execute(statement):
                return row[0]

    def get_stock_data(self, stock_data_id: str):
        with self.engine.connect() as connection:
            statement = text(f"SELECT * FROM stock_data WHERE stock_data_id = '{stock_data_id}'")
            for row in connection.execute(statement):
                return row

    def get_drawdowns(self, drawdown: Drawdown):
        drawdown_list = []

        with self.engine.connect() as connection:
            statement = text(f"""
                SELECT sd1.stock_data_id
                FROM stock_data AS sd1
                JOIN (
                    SELECT high, stock_data_id, date FROM stock_data
                ) AS sd2 
                ON sd2.stock_data_id = sd1.local_max_id
                WHERE sd1.stock_symbol = '{drawdown.stock_symbol}'
                AND ((sd2.high - sd1.low) / sd2.high)*100 > {drawdown.min}
                AND ((sd2.high - sd1.low) / sd2.high)*100 < {drawdown.max}
                AND ABS(sd1.date - sd2.date) > {drawdown.min}
                AND ABS(sd1.date - sd2.date) < {drawdown.max}
            """)

            for row in connection.execute(statement):
                drawdown_list.append(row[0])
            
            return drawdown_list
