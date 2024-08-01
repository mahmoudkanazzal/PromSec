import os
from flask import Flask, request, session, redirect
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
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    db_connection = get_db_connection()
    cursor = db_connection.cursor()

    cursor.execute("INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)", (stock_name, stock_quantity, username))
    db_connection.commit()

    cursor.close()
    db_connection.close()

    return redirect('/')

if __name__ == '__main__':
    app.run()