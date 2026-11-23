import os
import logging
from flask import Flask, request, session
import MySQLdb

logging.basicConfig(level=logging.ERROR)

secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable is required')

mysql_vars = {
    'MYSQL_HOST': os.getenv('MYSQL_HOST'),
    'MYSQL_USER': os.getenv('MYSQL_USER'),
    'MYSQL_PASSWORD': os.getenv('MYSQL_PASSWORD'),
    'MYSQL_DB': os.getenv('MYSQL_DB')
}
missing = [k for k, v in mysql_vars.items() if not v]
if missing:
    raise RuntimeError('Missing MySQL environment variables: ' + ','.join(missing))

app = Flask(__name__)
app.secret_key = secret_key

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    if not username:
        return 'unauthenticated', 401
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity:
        return 'missing_parameters', 400
    try:
        quantity = int(stock_quantity)
        if quantity <= 0:
            raise ValueError
    except ValueError:
        return 'invalid_quantity', 400
    conn = None
    try:
        conn = MySQLdb.connect(
            host=mysql_vars['MYSQL_HOST'],
            user=mysql_vars['MYSQL_USER'],
            passwd=mysql_vars['MYSQL_PASSWORD'],
            db=mysql_vars['MYSQL_DB']
        )
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)",
            (username, stock_name, quantity)
        )
        conn.commit()
        return 'successful', 200
    except MySQLdb.Error:
        logging.exception('Database error')
        if conn:
            conn.rollback()
        return 'failure', 500
    except Exception:
        logging.exception('Unexpected error')
        return 'failure', 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)