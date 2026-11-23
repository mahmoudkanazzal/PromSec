import os
import MySQLdb
import runpy
import sys
import io
import contextlib
from flask import Flask, request, session, Response

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'supersecret')

def _run_algorithm(script_path, action, username, stock_name, stock_quantity):
    original_argv = sys.argv[:]
    sys.argv = [script_path, action, username, stock_name, stock_quantity]
    captured = io.StringIO()
    try:
        with contextlib.redirect_stdout(captured):
            runpy.run_path(script_path, run_name="__main__")
    finally:
        sys.argv = original_argv
    return captured.getvalue()

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            passwd=os.getenv('DB_PASS', ''),
            db=os.getenv('DB_NAME', 'test')
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO db_table.order_table (username, stock_name, stock_quantity) VALUES (%s, %s, %s)",
            (username, stock_name, stock_quantity)
        )
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        return Response('An error occurred', status=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'algorithm.py'))
    output = _run_algorithm(script_path, 'buy', username, stock_name, stock_quantity)
    return Response(output, mimetype='text/plain')

if __name__ == '__main__':
    app.run()