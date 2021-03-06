from flask import Flask, render_template, request, jsonify
from database_helper import query_database, to_json, get_engines, get_runtime,save_query,get_saved_queries
from json import dumps
app = Flask(__name__)
engines = get_engines()


@app.route('/')
def main():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post():
    print(request.form)
    query_string = request.form['query_string']
    database_type = request.form['database_type']
    exceptionMessage = ''
    try:
        result = query_database(query_string, engines[database_type])
    except Exception as e:
        result = None
        exceptionMessage = str(e)
        print(f'Error: {exceptionMessage}')
    json_result, delim, summary, is_truncated = to_json(result) if result else ('-1', None, exceptionMessage, False)
    run_time = get_runtime()
    to_return = {
        'rows': json_result,
        'success': False if json_result == '-1' else True,
        'row_count': result.rowcount if result else '0',
        'run_time': str(run_time)[:5] if run_time else None,
        'delimiter': delim,
        'summary': summary,
        'is_truncated': is_truncated
    }
    save_query(query_string,to_return['run_time'],to_return['success'],to_return['row_count'],database_type,engines['mysql'])
    to_return = dumps(to_return)
    return to_return

@app.route('/get_query_history', methods=['POST'])
def get_query_history():
    return get_saved_queries(engines['mysql'])

if __name__ == '__main__':
    app.run(debug=True)

