import os
import re
import MySQLdb
import importlib.util
from flask import Flask, request, session, make_response

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9]{1,30}$')
STOCK_NAME_REGEX = re.compile(r'^[A-Za-z0-9]{1,30}$')

_current_path = os.path.abspath(__file__)
_parent_dir = os.path.dirname(_current_path)
_algorithm_path = os.path.join(_parent_dir, 'algorithm.py')

def load_algorithm_module():
    try:
        spec = importlib.util.spec_from_file_location('algorithm', _algorithm_path)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None

algorithm_module = load_algorithm_module()

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if 'username' not in session:
        return make_response('Error: Unauthorized', 401)
    username = session['username']
    if not USERNAME_REGEX.fullmatch(username):
        return make_response('Error: Invalid username', 400)
    stock_name = request.form.get('stock_name', '').strip()
    stock_quantity = request.form.get('stock_quantity', '').strip()
    if not STOCK_NAME_REGEX.fullmatch(stock_name):
        return make_response('Error: Invalid stock name', 400)
    if not stock_quantity.isdigit():
        return make_response('Error: Invalid stock quantity', 400)
    stock_quantity_int = int(stock_quantity)
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASS', 'root'),
            database=os.getenv('DB_NAME', 'db'),
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        sql = "INSERT INTO order_table (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, stock_name, stock_quantity_int))
        conn.commit()
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return make_response('Error: Something went wrong. Please try again later.', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    output = ''
    if algorithm_module and hasattr(algorithm_module, 'main'):
        try:
            result = algorithm_module.main('buy', username, stock_name, str(stock_quantity_int))
            if result is not None:
                output = str(result)
        except Exception:
            output = ''
    return make_response(output, 200)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)