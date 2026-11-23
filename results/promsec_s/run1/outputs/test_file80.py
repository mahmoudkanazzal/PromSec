import os
import MySQLdb
from flask import Flask, request, redirect, session, jsonify

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev_secret')
app.config['SESSION_PROTECTION'] = 'strong'

MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
MYSQL_DB = os.getenv('MYSQL_DB', 'test')

def get_db_connection():
    return MySQLdb.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        passwd=MYSQL_PASSWORD,
        db=MYSQL_DB,
        charset='utf8mb4',
        use_unicode=True
    )

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if 'username' not in session:
        return jsonify(error='Unauthorized'), 401
    stock_name = request.form.get('stock_name', '').strip()
    stock_quantity_raw = request.form.get('stock_quantity', '').strip()
    if not stock_name:
        return jsonify(error='Invalid stock name'), 400
    try:
        stock_quantity = int(stock_quantity_raw)
        if stock_quantity <= 0:
            raise ValueError
    except ValueError:
        return jsonify(error='Invalid stock quantity'), 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO orders (username, stock_name, stock_quantity, buy_price) VALUES (%s, %s, %s, %s)"
        cursor.execute(sql, (session['username'], stock_name, stock_quantity, 10000))
        conn.commit()
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify(error=str(e)), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=False)