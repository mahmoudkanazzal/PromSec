from __future__ import annotations
from os import getenv
import MySQLdb
import importlib.util as util
from pathlib import Path
from flask import Flask, request, session
from waitress import serve

app = Flask(__name__)
_secret = getenv('FLASK_SECRET_KEY')
if not _secret:
    raise RuntimeError('FLASK_SECRET_KEY environment variable is required')
app.secret_key = _secret

def _run_algorithm(action: str, username: str, stock_name: str, stock_quantity: str) -> str:
    alg_path = Path(__file__).resolve().parents[1] / 'algorithm.py'
    if not alg_path.is_file():
        raise FileNotFoundError(f'Algorithm file not found at {alg_path}')
    spec = util.spec_from_file_location('algorithm_module', str(alg_path))
    if spec is None or spec.loader is None:
        raise RuntimeError('Failed to load algorithm module spec')
    module = util.module_from_spec(spec)
    spec.loader.exec_module(module)
    func = getattr(module, 'process', None) or getattr(module, 'main', None)
    if not callable(func):
        raise RuntimeError('Algorithm module must define a callable process or main')
    return str(func(action, username, stock_name, stock_quantity))

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if 'username' not in session:
        return ('Unauthorized', 401)
    username = session['username']
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity:
        return ('Missing parameters', 400)
    if not stock_quantity.isdigit() or int(stock_quantity) <= 0:
        return ('Invalid stock quantity', 400)
    host = getenv('DB_HOST', 'localhost')
    user = getenv('DB_USER', 'root')
    password = getenv('DB_PASS', 'root')
    db = getenv('DB_NAME', 'db')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=password, db=db)
        cur = conn.cursor()
        sql = 'INSERT INTO db_table.order_table (username, stock_name, stock_quantity) VALUES (%s, %s, %s)'
        cur.execute(sql, (username, stock_name, stock_quantity))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        return (str(e), 500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    try:
        result = _run_algorithm('buy', username, stock_name, stock_quantity)
        return result
    except Exception as e:
        return (str(e), 500)

if __name__ == '__main__':
    host = getenv('HOST', '127.0.0.1')
    port_str = getenv('PORT')
    if not port_str:
        raise RuntimeError('PORT environment variable must be set')
    try:
        port = int(port_str)
    except ValueError:
        raise RuntimeError('PORT must be an integer')
    if not (1 <= port <= 65535):
        raise RuntimeError('PORT must be between 1 and 65535')
    serve(app, host=host, port=port)