import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        database=os.getenv('DB_NAME')
    )

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()

    if user:
        cursor.execute("UPDATE stocks SET quantity = quantity + %s WHERE user_id = %s AND stock_name = %s",
                       (stock_quantity, user[0], stock_name))
    else:
        cursor.execute("INSERT INTO users (username) VALUES (%s)", (username,))
        user_id = cursor.lastrowid
        cursor.execute("INSERT INTO stocks (user_id, stock_name, quantity) VALUES (%s, %s, %s)",
                       (user_id, stock_name, stock_quantity))

    db_connection.commit()
    cursor.close()
    db_connection.close()

    return 'Stock bought successfully'

if __name__ == '__main__':
    app.run()
