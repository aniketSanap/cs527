from flask import Flask, render_template, request, jsonify
from database_helper import get_engine, query_database, to_json
# from database_helper import 
app = Flask(__name__)
current_database = None
engine = None

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/post', methods=['POST'])
def post():
    global current_database, engine
    print(request.form)
    query_string = request.form['query_string']
    database_type = request.form['database_type']
    if database_type != current_database or engine is None:
        current_database = database_type
        engine = get_engine(database_type)

    result = query_database(query_string, engine)
    json_result = to_json(result)
    return json_result

if __name__ == '__main__':
    app.run(debug=True)