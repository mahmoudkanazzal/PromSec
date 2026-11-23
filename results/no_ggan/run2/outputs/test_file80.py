from flask import Flask, request, redirect, session, abort
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')
db_host = os.getenv('DB_HOST', 'localhost')
db_user = os.getenv('DB_USER', 'app_user')
db_password = os.getenv('DB_PASSWORD', '')
db_name = os.getenv('DB_NAME', 'db')

@app.route('/buy_order', methods=['POST'])
def buy_order():
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
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name, charset='utf8mb4', use_unicode=True)
        cursor = conn.cursor()
        sql = "INSERT INTO orders (username, stock_name, stock_quantity, buy_price) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, stock_name, quantity, 10000))
        conn.commit()
    except MySQLdb.Error:
        abort(500, description='Database error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()