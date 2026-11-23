from __future__ import annotations
import os
from contextlib import closing
from flask import Flask, request, session, Response
import MySQLdb

app = Flask(__name__)
secret = os.getenv('FLASK_SECRET_KEY')
if not secret:
    raise RuntimeError('FLASK_SECRET_KEY not set')
app.secret_key = secret
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

def failure_response() -> Response:
    return Response('failure', mimetype='text/plain')

def success_response() -> Response:
    return Response('successful', mimetype='text/plain')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name', '').strip()
    if not stock_name or len(stock_name) > 100:
        return failure_response()
    qty_str = request.form.get('stock_quantity', '').strip()
    try:
        stock_quantity = int(qty_str)
        if stock_quantity <= 0:
            return failure_response()
    except Exception:
        return failure_response()
    username = session.get('username', '').strip()
    if not username:
        return failure_response()
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    if not all([db_host, db_user, db_password, db_name]):
        raise RuntimeError('Database environment variables not set')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        with closing(conn.cursor()) as cursor:
            cursor.execute(
                'INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)',
                (username, stock_name, stock_quantity)
            )
        conn.commit()
        return success_response()
    except MySQLdb.Error:
        return failure_response()
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)