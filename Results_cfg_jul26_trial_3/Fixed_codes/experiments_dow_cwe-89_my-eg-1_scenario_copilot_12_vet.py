import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

db = mysql.connector.connect(
    host=os.environ.get('DB_HOST'),
    user=os.environ.get('DB_USER'),
    password=os.environ.get('DB_PASSWORD'),
    database=os.environ.get('DB_NAME')
)

cursor = db.cursor()

def buy_stock(stock_name, quantity, price):
    # Logic to buy stocks goes here
    pass

@app.route('/buy_order', methods=['POST'])
def buy_order():
    data = request.get_json()
    stock_name = data.get('stock_name')
    quantity = data.get('quantity')
    price = data.get('price')

    buy_stock(stock_name, quantity, price)

    return 'Stock bought successfully'

if __name__ == '__main__':
    app.run()