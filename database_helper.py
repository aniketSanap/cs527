import sqlalchemy
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from config import connection_strings, row_limiter
import pandas as pd
from time import time
from utils import make_unique


run_time = None

def get_engine(db_type, conn_str=None):
    """
    Returns an engine object using a connection string
    db_type: One of ["mysql", "redshift"]
    conn_str (optional): create object using this parameter if given else use strings from config
    """
    if conn_str is None:
        if db_type in connection_strings:
            conn_str = connection_strings[db_type]
        else:
            raise KeyError(f'{db_type} does not exist in config file!')

    return create_engine(conn_str, pool_pre_ping=True)

def query_database(query, engine):
    """
    Returns the result of `query` on `engine`
    query: Query input by user
    engine: engine object (either from mysql/redshift)
    """
    try:
        with engine.connect() as conn:
            result = conn.execute(text(query))

    except sqlalchemy.exc.SQLAlchemyError as ex:
        result = None
        raise ex

    return result

def add_index(df):
    """
    Used to add metrics to a summary of a table and rearrange the table
    df: pandas dataframe
    """
    cols = list(df.columns)
    df['metric'] = df.index
    cols = ['metric'] + cols
    return df[cols]

def to_json(result):
    """
    Converts sqlalchemy result to json
    result: result

    Returns:
    json string: json string of output to be displayed on the front end
    delimiter: Used to differentiate between same column names in key value pairs
    summary: summary of the output query
    is_truncated: Boolean value to tell if the result table has been truncated or not
    """
    try:
        is_truncated = False
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
        if len(df) > row_limiter:
            df = df[:row_limiter]
            is_truncated = True
        summary = df.describe().round(2)
        summary = add_index(summary)
        unique_cols, delim = make_unique(df.columns)
        summary_unique_cols, delim = make_unique(summary.columns)
        df.columns = unique_cols
        summary.columns = summary_unique_cols
        return df.to_json(orient='records'), delim, summary.to_json(orient='records'), is_truncated
    except sqlalchemy.exc.ResourceClosedError:
        # For DML queries
        return '[]', None, None, False

    except Exception as e:
        print(e)
        # For errors
        return '-1', None, None, False

def get_engines(database_types=['mysql', 'redshift']):
    """
    Returns an engine object of every given type
    """
    engines = {}
    for db_type in database_types:
        engines[db_type] = get_engine(db_type)
    return engines

@event.listens_for(Engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    """
    Runs before the cursor executes the query
    """
    global run_time
    run_time = None
    conn.info.setdefault('query_start_time', []).append(time())

@event.listens_for(Engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement,
                        parameters, context, executemany):
    """
    Runs after the cursor executes the query
    """
    global run_time
    run_time = time() - conn.info['query_start_time'].pop(-1)

def get_runtime():
    """
    Returns run time of the query
    """
    return run_time

def save_query(query_text,query_runtime,query_is_success,records_returned,database_used,engine):
    """
    Saves the query entered by the user into the database
    """
    try:
        with engine.connect() as conn:
            sql = "INSERT INTO saved_queries(query_text,query_runtime,query_is_success,query_records_returned,database_used,created_date) values(%s,%s,%s,%s,%s,CURRENT_TIMESTAMP())"
            result = conn.execute(sql,(query_text,query_runtime,query_is_success,records_returned,database_used))

    except sqlalchemy.exc.SQLAlchemyError as e:
        print(e)
        result = None

    return result

def get_saved_queries(engine):
    """
    Returns last 100 queries from the database
    """
    try:
        with engine.connect() as conn:
            sql = "select query_text, query_runtime, case when query_is_success then 'True' else 'False' END as query_is_success,query_records_returned,database_used,DATE_FORMAT(CONVERT_TZ(created_date,'GMT','EST'),'%%m/%%d/%%Y %%H:%%i:%%s') as created_date from saved_queries order by query_id desc limit 100;"

            result = conn.execute(sql)

    except sqlalchemy.exc.SQLAlchemyError:
        result = None

    if result:
        return pd.DataFrame(result.fetchall(), columns=result.keys()).to_json(orient='records')
    return None