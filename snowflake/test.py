from sqlalchemy import create_engine, text
from helpers.read_config import read_config

config = read_config('Snowflake')

engine = create_engine(
    'snowflake://{user}:{password}@{account_identifier}/'.format(
        user=config['User'],
        password=config['Password'],
        account_identifier=config['AccountIdentifier'],
    )
)
try:
    connection = engine.connect()
    results = connection.execute(text('select current_version()')).fetchone()
    print(results[0])
finally:
    connection.close()
    engine.dispose()