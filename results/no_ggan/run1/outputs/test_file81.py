import os
import sys
import MySQLdb
from flask import Flask, request, session, abort

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    try:
        return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)
    except MySQLdb.Error:
        abort(500, description="Database connection failed.")

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity_raw = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity_raw:
        abort(400, description="Missing required parameters.")
    username = session.get('username')
    if not username:
        abort(401, description="User not authenticated.")
    try:
        stock_quantity = int(stock_quantity_raw)
        if stock_quantity <= 0:
            raise ValueError
    except ValueError:
        abort(400, description="Invalid stock quantity. Must be a positive integer.")
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT stock_quantity FROM user_portfolio WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            existing_quantity = row[0] if row[0] is not None else 0
            new_quantity = existing_quantity + stock_quantity
            cursor.execute("UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s", (new_quantity, username))
            conn.commit()
            return "updated"
        else:
            cursor.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, stock_quantity))
            conn.commit()
            return "initialized"
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()