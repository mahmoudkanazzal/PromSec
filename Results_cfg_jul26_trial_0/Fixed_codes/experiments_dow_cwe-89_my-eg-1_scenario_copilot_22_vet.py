import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASSWORD', 'root'),
        db=os.getenv('DB_NAME', 'db')
    )

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute("SELECT * FROM user_portfolio WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user:
        cursor.execute("UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s", (stock_quantity, username))
    else:
        cursor.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, stock_quantity))

    db_connection.commit()
    cursor.close()
    db_connection.close()

    return 'Stock bought successfully'

if __name__ == '__main__':
    app.run()