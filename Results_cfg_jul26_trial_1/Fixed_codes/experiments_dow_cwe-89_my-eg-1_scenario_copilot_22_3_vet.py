import os
from flask import Flask, request, session, jsonify
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

def db_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    if 'username' not in session:
        return jsonify({'message': 'User not logged in'})

    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session['username']

    try:
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM portfolio WHERE username = %s AND stock_name = %s", (username, stock_name))
        result = cursor.fetchone()

        if result:
            cursor.execute("UPDATE portfolio SET stock_quantity = stock_quantity + %s WHERE username = %s AND stock_name = %s", (stock_quantity, username, stock_name))
        else:
            cursor.execute("INSERT INTO portfolio (username, stock_name, stock_quantity) VALUES (%s, %s, %s)", (username, stock_name, stock_quantity))

        conn.commit()
        conn.close()

        return jsonify({'message': 'Stock bought successfully'})

    except mysql.connector.Error as e:
        return jsonify({'message': 'Error buying stock'})

if __name__ == '__main__':
    app.run()