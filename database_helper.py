from sqlalchemy import create_engine, text
from config import connection_strings
import pandas as pd


def get_engine(db_type, conn_str=None):
    if conn_str is None:
        if db_type in connection_strings:
            conn_str = connection_strings[db_type]
        else:
            raise KeyError(f'{db_type} does not exist in config file!')

    return create_engine(conn_str)

def query_database(query, engine):
    with engine.connect() as conn:
        result = conn.execute(text(query))

    return result

def to_json(result):
    # return (pd.DataFrame(result.fetchall(), columns=result.keys())
    #         .to_json(orient='index'))

    # return pd.DataFrame(result.fetchall(), columns=result.keys()).to_html(index=False)
    return pd.DataFrame(result.fetchall(), columns=result.keys()).to_json(orient='records')

def get_engines(database_types=['mysql', 'redshift']):
    engines = {}
    for db_type in database_types:
        engines[db_type] = get_engine(db_type)

    return engines