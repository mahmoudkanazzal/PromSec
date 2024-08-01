import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

def establish_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME')
    )

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    db = establish_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT * FROM user_portfolio WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user:
        cursor.execute("UPDATE user_portfolio SET stock_quantity = stock_quantity + %s WHERE username = %s AND stock_name = %s", (stock_quantity, username, stock_name))
    else:
        cursor.execute("INSERT INTO user_portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)", (username, stock_name, stock_quantity))

    db.commit()
    cursor.close()
    db.close()

    return 'Stock bought successfully'

if __name__ == '__main__':
    app.run()
