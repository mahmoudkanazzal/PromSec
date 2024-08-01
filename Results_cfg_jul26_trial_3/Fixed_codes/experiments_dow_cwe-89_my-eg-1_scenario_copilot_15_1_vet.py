import os
from flask import Flask, request, redirect
import mysql.connector

app = Flask(__name__)

def insert_order(username, stock_name, stock_quantity):
    db = mysql.connector.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', 'root'),
        database=os.getenv('DB_NAME', 'db')
    )
    cursor = db.cursor()
    cursor.execute("INSERT INTO orders (username, stock_name, stock_quantity, buy_price) VALUES (%s, %s, %s, 0)", (username, stock_name, stock_quantity))
    db.commit()
    db.close()

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = request.form.get('username')
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    
    insert_order(username, stock_name, stock_quantity)
    
    return redirect('/')

if __name__ == '__main__':
    app.run()