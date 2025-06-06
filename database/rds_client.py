import boto3
import json
from botocore.exceptions import ClientError
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

from helpers.read_config import read_config
from database.pydantic_models import *
from computation.drawdown import Drawdown

def get_secret():
        secret_name = config["SecretName"]
        region_name = "us-west-1"

        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            # For a list of exceptions thrown, see
            # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
            raise e

        secret = get_secret_value_response['SecretString']
        return secret

config = read_config('RDS')
password = json.loads(get_secret())['password']

url = URL.create(
    drivername="postgresql+psycopg2",
    username=config['User'],
    password=password,
    host=config['Host'],
    port=config['Port'],
    database='market_data'
)

engine = create_engine(url, pool_size=2, max_overflow=2)
Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class RdsClient:

    def __init__(self):
        self.engine = engine
        self.stock_data_id_list = []

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
    
    def insert_to_split_data_table(self, split_data: SplitData):
        with self.engine.connect() as connection:
            connection.execute(
                text("""
                    INSERT INTO split_data (date, stock_symbol, split_factor)
                    SELECT :date, :stock_symbol, :split_factor;
                """),
                {
                    "date": split_data.date,
                    "stock_symbol": split_data.stock_symbol,
                    "split_factor": split_data.split_factor
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
    
    def split_data_exists(self, stock_symbol: str, date: str):
        with self.engine.connect() as connection:
            statement = text(f"""
                SELECT * FROM split_data 
                WHERE stock_symbol = '{stock_symbol}'
                AND date = '{date}'
            """)
            for row in connection.execute(statement):
                return True
            
            return False
        
    def get_split_factor(self, stock_symbol: str, date: str):
        with self.engine.connect() as connection:
            statement = text(f"""
                SELECT exp(sum(ln(split_factor))) FROM split_data 
                WHERE stock_symbol = '{stock_symbol}'
                AND date <= '{date}'
            """)
            for row in connection.execute(statement):

                # row[0] = none if table empty
                if row[0]:
                    return row[0]
                
                return 1
    
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

    def get_drawdowns(self, drawdown: Drawdown) -> dict:
        drawdown_dict = {}

        statement = text("""
            SELECT sd1.stock_data_id, sd1.date, sd1.low, sd2.high, ABS(sd1.date - sd2.date) AS drawdown_period, sd3.max_drawdown
            FROM stock_data AS sd1
            JOIN (
                SELECT high, stock_data_id, date FROM stock_data
            ) AS sd2 
            ON sd2.stock_data_id = sd1.local_max_id
            JOIN (
                SELECT MIN(low) as max_drawdown, local_max_id
                FROM stock_data
                GROUP BY local_max_id
            ) as sd3
            ON sd3.local_max_id = sd1.local_max_id
            WHERE sd1.stock_symbol = :stock_symbol
            AND ((sd2.high - sd1.low) / sd2.high)*100 >= :min
            AND ((sd2.high - sd1.low) / sd2.high)*100 <= :max
            AND ABS(sd1.date - sd2.date) >= :duration_days_min
            AND ABS(sd1.date - sd2.date) <= :duration_days_max
        """)

        with Session() as session:
            result = session.execute(statement, {
                "stock_symbol": drawdown.stock_symbol,
                "min": drawdown.min,
                "max": drawdown.max,
                "duration_days_min": drawdown.duration_days_min,
                "duration_days_max": drawdown.duration_days_max
            })

            for row in result:
                drawdown_dict[row[0]] = {}
                drawdown_dict[row[0]]["drawdown_date"] = row[1]
                drawdown_dict[row[0]]["low"] = row[2]
                drawdown_dict[row[0]]["local_max"] = row[3]
                drawdown_dict[row[0]]['drawdown_period_days'] = row[4]
                drawdown_dict[row[0]]['max_drawdown'] = row[5]
        
        return drawdown_dict
    
    # perplexity.ai just doubled the speed of this function :D
    def get_recovery_data(self, drawdown_data: dict, drawdown: Drawdown, recovery_percentage: int) -> dict:
        
        drawdown_list = []
        for stock_data_id, info in drawdown_data.items():
            target = self.calculate_target(info, recovery_percentage)
            drawdown_list.append((stock_data_id, info["drawdown_date"], target))

        if not drawdown_list:
            return {}

        values_clause = ", ".join(
            f"('{stock_data_id}', '{drawdown_date}'::date, {target})"
            for stock_data_id, drawdown_date, target in drawdown_list
        )

        statement = text(f"""
            WITH drawdowns(stock_data_id, drawdown_date, target) AS (
                VALUES {values_clause}
            )
            SELECT d.stock_data_id, MIN(s.date) AS recovery_date
            FROM drawdowns d
            JOIN stock_data s
                ON s.stock_symbol = :stock_symbol
                AND s.high >= d.target
                AND s.date > d.drawdown_date
            GROUP BY d.stock_data_id
        """)

        with Session() as session:
            result = session.execute(statement, {"stock_symbol": drawdown.stock_symbol})

            data = {}
            for row in result:
                stock_data_id, recovery_date = row
                if recovery_date:
                    info = drawdown_data[stock_data_id]
                    info["recovery_date"] = recovery_date
                    data[stock_data_id] = info
        
        return data

    def calculate_target(self, drawdown_info: dict, recovery_percentage: int):
        drawdown_diff = drawdown_info["local_max"] - drawdown_info["low"]
        target_gain = (drawdown_diff * recovery_percentage) / 100
        target = drawdown_info["low"] + target_gain
        return target
