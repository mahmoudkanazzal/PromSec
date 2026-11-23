from flask import Flask, request, redirect, session, abort
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev')

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name:
        abort(400, description='Missing stock_name')
    if not stock_quantity:
        abort(400, description='Missing stock_quantity')
    if not username:
        abort(400, description='User not authenticated')
    try:
        stock_quantity_int = int(stock_quantity)
    except (ValueError, TypeError):
        abort(400, description='stock_quantity must be an integer')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    if not db_user or not db_password or not db_name:
        abort(500, description='Database configuration missing')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host,
                               user=db_user,
                               passwd=db_password,
                               db=db_name,
                               charset='utf8mb4',
                               use_unicode=True)
        cursor = conn.cursor()
        sql = """INSERT INTO orders (username, stock_name, stock_quantity, buy_price)
                 VALUES (%s, %s, %s, %s)"""
        cursor.execute(sql, (username, stock_name, stock_quantity_int, 10000))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()