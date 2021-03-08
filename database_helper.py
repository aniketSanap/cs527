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

def add_index(df):
    cols = list(df.columns)
    df['metric'] = df.index
    cols = ['metric'] + cols
    return df[cols]

def to_json(result):
    """Converts sqlalchemy result to json"""
    try:
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        summary = df.describe().round(2)
        summary = add_index(summary)
        unique_cols, delim = make_unique(df.columns)
        df.columns = unique_cols
        return df.to_json(orient='records'), delim, summary.to_json(orient='records')
    except sqlalchemy.exc.ResourceClosedError:
        return '[]', None, None

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

def save_query(query_text,query_runtime,query_is_success,records_returned,engine):
    
    try:
        with engine.connect() as conn:
            sql = "INSERT INTO saved_queries(query_text,query_runtime,query_is_success,query_records_returned,created_date) values(%s,%s,%s,%s,CURRENT_TIMESTAMP())"
            result = conn.execute(sql,(query_text,query_runtime,query_is_success,records_returned))

    except sqlalchemy.exc.SQLAlchemyError:
        result = None

    return result

def get_saved_queries(engine):
    try:
        with engine.connect() as conn:
            sql = "SELECT * from saved_queries order by created_date desc limit 10;"
            result = conn.execute(sql)

    except sqlalchemy.exc.SQLAlchemyError:
        result = None

    if result:
        return pd.DataFrame(result.fetchall(), columns=result.keys()).to_json(orient='records')
    return None