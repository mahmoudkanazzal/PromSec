import os
from flask import Flask, request, redirect
import mysql.connector

app = Flask(__name__)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = request.form.get('username')

    connection = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'root'),
        database=os.getenv('DB_DATABASE', 'db')
    )

    cursor = connection.cursor()
    cursor.execute("INSERT INTO orders (stock_name, stock_quantity, username, buy_price) VALUES (%s, %s, %s, %s)", (stock_name, stock_quantity, username, 10000))

    connection.commit()

    cursor.close()
    connection.close()

    return redirect('/')

if __name__ == '__main__':
    app.run()