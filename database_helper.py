import sqlalchemy
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from config import connection_strings
import pandas as pd
from time import time
from utils import make_unique


run_time = None

def get_engine(db_type, conn_str=None):
    if conn_str is None:
        if db_type in connection_strings:
            conn_str = connection_strings[db_type]
        else:
            raise KeyError(f'{db_type} does not exist in config file!')

    return create_engine(conn_str)

def query_database(query, engine):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))

    except sqlalchemy.exc.SQLAlchemyError:
        result = None

    return result

def to_json(result):
    """Converts sqlalchemy result to json"""
    try:
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        unique_cols, delim = make_unique(df.columns)
        df.columns = unique_cols
        return df.to_json(orient='records'), delim
    except sqlalchemy.exc.ResourceClosedError:
        return '[]', None

def get_engines(database_types=['mysql', 'redshift']):
    engines = {}
    for db_type in database_types:
        engines[db_type] = get_engine(db_type)

    return engines

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    global run_time
    run_time = None
    conn.info.setdefault('query_start_time', []).append(time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    global run_time
    run_time = time() - conn.info['query_start_time'].pop(-1)

def get_runtime():
    return run_time