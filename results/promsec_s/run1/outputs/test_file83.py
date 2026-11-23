import os
from flask import Flask, request, session
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'change_me')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = session.get('username')
    if not username:
        return 'unauthenticated', 401
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    try:
        qty = int(stock_quantity)
    except (TypeError, ValueError):
        return 'invalid quantity', 400
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME')
    )
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT stock_quantity FROM user_portfolio WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            current_qty = int(row[0])
            new_qty = current_qty + qty
            cursor.execute("UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s", (new_qty, username))
            conn.commit()
            return 'updated'
        else:
            cursor.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, qty))
            conn.commit()
            return 'initialized'
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()