from flask import Flask, request, redirect, session
import os, sys, MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'test')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        return 'error'
    try:
        qty = int(stock_quantity)
    except:
        return 'error'
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT stock_quantity FROM user_portfolio WHERE username=%s AND stock_name=%s', (username, stock_name))
        row = cur.fetchone()
        if row:
            try:
                existing_qty = int(row[0])
            except:
                existing_qty = 0
            new_qty = existing_qty + qty
            cur.execute('UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s AND stock_name=%s', (new_qty, username, stock_name))
            conn.commit()
            return 'updated'
        else:
            cur.execute('INSERT INTO user_portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)', (username, stock_name, qty))
            conn.commit()
            return 'initialized'
    except:
        return 'error'
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()