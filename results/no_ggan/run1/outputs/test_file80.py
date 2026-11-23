from flask import Flask, request, redirect, session
import os
import MySQLdb
import logging

logging.basicConfig(level=logging.INFO)
app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        logging.warning("Missing required form fields.")
        return redirect('/', code=400)
    try:
        stock_quantity_int = int(stock_quantity)
        if stock_quantity_int <= 0:
            raise ValueError
    except Exception:
        logging.warning("Invalid stock_quantity: %s" % stock_quantity)
        return redirect('/', code=400)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        buy_price = 10000
        sql = "INSERT INTO orders (username, stock_name, stock_quantity, buy_price) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (username, stock_name, stock_quantity_int, buy_price))
        conn.commit()
    except MySQLdb.Error as e:
        logging.error("Database error while inserting order: %s" % e)
        if conn:
            conn.rollback()
        return redirect('/', code=500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')