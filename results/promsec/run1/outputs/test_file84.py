from flask import Flask, request, session
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'testdb')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not username:
        return 'Unauthorized', 401
    try:
        qty = int(stock_quantity)
        if qty <= 0:
            raise ValueError
    except (ValueError, TypeError):
        return 'Invalid quantity', 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stock_quantity FROM user_portfolio WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row:
            current_qty = int(row[0])
            new_qty = current_qty + qty
            cursor.execute('UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s', (new_qty, username))
            conn.commit()
            return 'updated'
        else:
            cursor.execute('INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)', (username, qty))
            conn.commit()
            return 'initialized'
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()