import os
from flask import Flask, request, session, redirect
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    connection = mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'root'),
        passwd=os.environ.get('DB_PASS', 'root'),
        db=os.environ.get('DB_NAME', 'db')
    )
    cursor = connection.cursor()

    cursor.execute("INSERT INTO buy_orders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)", (stock_name, stock_quantity, username))
    connection.commit()

    cursor.close()
    connection.close()

    return redirect('/')

if __name__ == '__main__':
    app.run()