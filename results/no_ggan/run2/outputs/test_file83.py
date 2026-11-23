import os
from flask import Flask, request, session, abort, jsonify
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_this_secret')

def _get_db_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASSWORD', 'root'),
        db=os.getenv('DB_NAME', 'db')
    )

def _validate_stock_quantity(value):
    try:
        qty = int(value)
        if qty < 0:
            raise ValueError
        return qty
    except Exception:
        abort(400, description='stock_quantity must be a non-negative integer')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    if 'username' not in session:
        abort(401)
    username = session['username']
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    if not stock_name or stock_quantity is None:
        abort(400, description='stock_name and stock_quantity are required')
    quantity = _validate_stock_quantity(stock_quantity)
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT stock_quantity FROM user_portfolio WHERE username=%s AND stock_name=%s',
            (username, stock_name)
        )
        row = cursor.fetchone()
        if row:
            existing_quantity = row[0]
            new_quantity = existing_quantity + quantity
            cursor.execute(
                'UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s AND stock_name=%s',
                (new_quantity, username, stock_name)
            )
            conn.commit()
            return jsonify(status='updated', stock_quantity=new_quantity)
        else:
            cursor.execute(
                'INSERT INTO user_portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)',
                (username, stock_name, quantity)
            )
            conn.commit()
            return jsonify(status='initialized', stock_quantity=quantity)
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()