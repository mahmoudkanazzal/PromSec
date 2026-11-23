from flask import Flask, request, session
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    if not username:
        return 'Missing username in session', 400
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_quantity or not stock_quantity.isdigit() or int(stock_quantity) <= 0:
        return 'Invalid stock_quantity', 400
    qty = int(stock_quantity)
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT stock_quantity FROM user_portfolio WHERE username = %s', (username,))
        row = cur.fetchone()
        if row:
            current_qty = row[0] or 0
            new_qty = current_qty + qty
            cur.execute('UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s', (new_qty, username))
            conn.commit()
            return 'updated', 200
        else:
            cur.execute('INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)', (username, qty))
            conn.commit()
            return 'initialized', 201
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()