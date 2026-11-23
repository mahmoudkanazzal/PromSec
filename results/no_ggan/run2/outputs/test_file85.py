from flask import Flask, request, session, jsonify
import os
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24).hex()

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        return jsonify({'status': 'failure', 'error': 'Missing required fields'}), 400
    try:
        quantity_int = int(stock_quantity)
        if quantity_int <= 0:
            raise ValueError
    except ValueError:
        return jsonify({'status': 'failure', 'error': 'Invalid stock_quantity'}), 400
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, stock_name, quantity_int))
        conn.commit()
        return jsonify({'status': 'successful'}), 200
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'failure', 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()