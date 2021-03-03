from flask import Flask, render_template, request, jsonify
from database_helper import get_engine, query_database, to_json, get_engines
# from database_helper import 
app = Flask(__name__)
current_database = None
current_engine = None
engines = get_engines()


@app.route('/')
def main():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post():
    global current_database, current_engine, engines
    # print(request.form)
    query_string = request.form['query_string']
    database_type = request.form['database_type']
    if database_type != current_database:
        current_database = database_type
        current_engine = engines[database_type]
        
    print(f'query_string: {query_string}, current_database: {current_database}')
    result = query_database(query_string, current_engine)
    json_result = to_json(result)
    return json_result

if __name__ == '__main__':
    app.run(debug=True)