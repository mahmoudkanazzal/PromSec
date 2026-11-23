from flask import Flask, request, redirect, session, abort
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

def get_db_connection():
    """Create and return a MySQLdb connection using environment variables."""
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        abort(400, description='Missing stock_name, stock_quantity, or username')
    try:
        quantity = int(stock_quantity)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        abort(400, description='stock_quantity must be a positive integer')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)"
        cursor.execute(sql, (stock_name, quantity, username))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()