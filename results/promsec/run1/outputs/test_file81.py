import os
import sys
import MySQLdb
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'testdb')
    return MySQLdb.connect(host=host, user=user, password=password, db=db, charset='utf8mb4', cursorclass=MySQLdb.cursors.DictCursor)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if 'username' not in session:
        return 'unauthenticated', 401
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_quantity or not stock_quantity.isdigit() or int(stock_quantity) <= 0:
        return 'invalid quantity', 400
    qty = int(stock_quantity)
    username = session['username']
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT stock_quantity FROM user_portfolio WHERE username=%s", (username,))
        row = cursor.fetchone()
        if row:
            current_qty = int(row['stock_quantity']) if row['stock_quantity'] is not None else 0
            new_qty = current_qty + qty
            cursor.execute("UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s", (new_qty, username))
            conn.commit()
            return 'updated'
        else:
            cursor.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, qty))
            conn.commit()
            return 'initialized'
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()