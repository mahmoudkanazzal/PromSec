import os
from flask import Flask, request, redirect, url_for, session, make_response
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

@app.route('/')
def home():
    return 'Home Page'

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name', '').strip()
    stock_quantity_raw = request.form.get('stock_quantity', '').strip()
    username = session.get('username')
    if not stock_name or not stock_quantity_raw or not username:
        return make_response('Invalid input', 400)
    try:
        stock_quantity = int(stock_quantity_raw)
        if stock_quantity <= 0:
            raise ValueError
    except ValueError:
        return make_response('Invalid input', 400)
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_name = os.getenv('DB_NAME')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        sql = "INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)"
        cursor.execute(sql, (stock_name, stock_quantity, username))
        conn.commit()
    except Exception:
        if conn:
            conn.rollback()
        return make_response('An error occurred', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run()