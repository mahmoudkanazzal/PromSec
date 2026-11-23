import os
from flask import Flask, request, session, abort, jsonify
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change-me')

def _get_db_connection():
    """
    Establish and return a MySQLdb connection using credentials from environment variables.
    Raises RuntimeError if DB_USER, DB_PASSWORD, or DB_NAME are not set.
    """
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_NAME')
    missing = [var for var, val in (('DB_USER', user), ('DB_PASSWORD', password), ('DB_NAME', db)) if not val]
    if missing:
        raise RuntimeError(f"Missing required database environment variables: {', '.join(missing)}")
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    """
    Process a buy order by validating input, updating or inserting the user's portfolio,
    and returning a JSON response. Handles input validation, database errors, and ensures
    the connection is closed.
    """
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')
    if not stock_name or not stock_quantity or not username:
        abort(400, description='stock_name, stock_quantity, and username are required.')
    try:
        quantity = int(stock_quantity)
        if quantity <= 0:
            abort(400, description='stock_quantity must be a positive integer.')
    except ValueError:
        abort(400, description='stock_quantity must be an integer.')
    conn = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT stock_quantity FROM user_portfolio WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row:
            existing_quantity = row[0] or 0
            new_quantity = existing_quantity + quantity
            cursor.execute('UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s', (new_quantity, username))
            conn.commit()
            response = {"status": "updated", "username": username, "stock_quantity": new_quantity}
        else:
            cursor.execute('INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)', (username, quantity))
            conn.commit()
            response = {"status": "initialized", "username": username, "stock_quantity": quantity}
        return jsonify(response), 200
    except MySQLdb.Error:
        abort(500, description='Database error.')
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()