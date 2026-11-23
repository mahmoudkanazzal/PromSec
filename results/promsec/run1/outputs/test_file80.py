from flask import Flask, request, redirect, session
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        return redirect('/')
    try:
        stock_quantity_int = int(stock_quantity)
    except ValueError:
        return redirect('/')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_password = os.getenv('DB_PASSWORD', '')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        sql = "INSERT INTO orders (username, stock_name, stock_quantity, buy_price) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, stock_name, stock_quantity_int, 10000))
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run()