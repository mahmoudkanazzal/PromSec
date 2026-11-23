import os
from flask import Flask, request, session, jsonify, abort
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if 'username' not in session:
        abort(401, description='Authentication required')
    username = session['username']
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or not stock_quantity:
        abort(400, description='Missing stock_name or stock_quantity')
    try:
        stock_quantity_int = int(stock_quantity)
        if stock_quantity_int <= 0:
            raise ValueError
    except ValueError:
        abort(400, description='stock_quantity must be a positive integer')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, stock_name, stock_quantity_int))
        conn.commit()
        return jsonify({'status': 'success'}), 200
    except MySQLdb.Error as e:
        if conn:
            conn.rollback()
        return jsonify({'status': 'failure', 'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)