import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

def connect_to_database():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_DATABASE
    )

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    if 'username' not in session:
        return 'User not logged in', 401

    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session['username']

    try:
        db = connect_to_database()
        cursor = db.cursor()

        # Perform necessary operations to update user's stock portfolio

        db.commit()
        cursor.close()
        db.close()

        return 'Stock bought successfully', 200
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run()