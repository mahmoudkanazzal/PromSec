import os
import sys
from flask import Flask, request, abort, redirect, session
import MySQLdb

flask_secret_key = os.getenv('FLASK_SECRET_KEY')
if not flask_secret_key:
    raise RuntimeError('FLASK_SECRET_KEY not set')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
port = int(os.getenv('PORT', '5000'))

app = Flask(__name__)
app.secret_key = flask_secret_key
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    if not username:
        abort(401)
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity:
        abort(400)
    try:
        quantity = int(stock_quantity)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        abort(400)
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host='localhost', user=db_user, password=db_password, db='db', charset='utf8mb4', use_unicode=True)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO orders (username, stock_name, stock_quantity, buy_price) VALUES (%s, %s, %s, %s)",
            (username, stock_name, quantity, 10000)
        )
        conn.commit()
        return redirect('/')
    except MySQLdb.Error as e:
        print(e, file=sys.stderr)
        abort(500)
    finally:
        try:
            if cur:
                cur.close()
        finally:
            if conn:
                conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=port)