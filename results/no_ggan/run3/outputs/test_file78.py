import os
import sys
import logging
from flask import Flask, request, redirect, session, abort
import MySQLdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'db')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        logger.warning('Missing required fields')
        abort(400, description='Missing required fields')
    try:
        quantity = int(stock_quantity)
        if quantity <= 0:
            raise ValueError
    except Exception:
        logger.warning('Invalid stock quantity')
        abort(400, description='Invalid stock quantity')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=DB_HOST,
                               user=DB_USER,
                               passwd=DB_PASSWORD,
                               db=DB_NAME,
                               charset='utf8mb4',
                               use_unicode=True)
        cursor = conn.cursor()
        sql = 'INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)'
        cursor.execute(sql, (stock_name, quantity, username))
        conn.commit()
    except MySQLdb.Error as e:
        logger.error('Database error: %s', e)
        abort(500, description='Internal server error')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)