import sqlalchemy
from sqlalchemy import create_engine, text, event
from sqlalchemy.engine import Engine
from config import connection_strings, row_limiter
import pandas as pd
from time import time
from utils import make_unique
import os
import pyodbc

run_time = None
mongo_run_time= None
mongo_row_count = -1
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


def get_mongo_data(query, db_type) :
    
    if db_type in connection_strings:
            conn_str = connection_strings[db_type]
    else:
        raise KeyError(f'{db_type} does not exist in config file!')
    con = pyodbc.connect(conn_str)
    cur = con.cursor()
    cur.execute(query)
    res = pd.DataFrame(cur.fetchall())
    #print(res)
    return res

def add_index(df):
    """
    Used to add metrics to a summary of a table and rearrange the table
    df: pandas dataframe
    """
    cols = list(df.columns)
    df['metric'] = df.index
    cols = ['metric'] + cols
    return df[cols]


def to_json(result, is_mongo_query=False):
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
        global mongo_row_count,mongo_run_time
        if is_mongo_query:
            if result.rowcount ==-1:
                tick = time()
                cols = [column[0] for column in result.description]
                rows = (tuple(t) for t in result.fetchall())
                df = pd.DataFrame(rows,columns=cols)
                tock = time()
                mongo_run_time = tock-tick
                mongo_row_count  = len(df)
            else:
                return '[]', None, None, False
        else:
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


def get_runtime(is_mongo=False):
    """
    Returns run time of the query
    """
    if is_mongo:
        return mongo_run_time
    return run_time


def save_query(query_text, query_runtime, query_is_success, records_returned, database_used, engine):
    """
    Saves the query entered by the user into the database
    """
    try:
        with engine.connect() as conn:
            sql = "INSERT INTO saved_queries(query_text,query_runtime,query_is_success,query_records_returned,database_used,created_date) values(%s,%s,%s,%s,%s,CURRENT_TIMESTAMP())"
            result = conn.execute(
                sql, (query_text, query_runtime, query_is_success, records_returned, database_used))

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

def query_mongo_database(query_string,db_type):
    
    con = pyodbc.connect(connection_strings[db_type])
    cur = con.cursor()
    result=cur.execute(query_string)
    
    return result


def is_data_empty(result, is_dataframe):
    if is_dataframe:
        if result is None:
            return False
        return result.empty
    else:
        print("is_data_empty", result)
        if result:
            return False
        else:
            return True


def get_rowcount(result,is_mongo):
    if is_mongo:
        if not result:
            return '-1'
        return max(mongo_row_count,result.rowcount)
    return result.rowcount if result else '0'


def get_mongodb_query(query_string):
    mongodb_file = 'mongodb_query.json'
    sql_file = 'sql_query.sql'
    mongo_query = ''
    if query_string.strip() != '':
        if os.path.exists(mongodb_file):
            os.remove(mongodb_file)
        if os.path.exists(sql_file):
            os.remove(sql_file)
        with open(sql_file, 'w') as f:
            f.write(query_string)
        java_command = f'java -jar Sql.jar -s {sql_file} -d {mongodb_file}'
        os.system(java_command)
    if os.path.exists(mongodb_file):
        with open(mongodb_file, 'r') as f:
            mongo_query = f.read()
    return mongo_query.replace("******Mongo Query:*********", "").strip()