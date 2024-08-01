import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

db = mysql.connector.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    database=db_name
)

cursor = db.cursor()

@app.route('/buy_order', methods=['POST'])
def buy_order():
    data = request.get_json()
    product = data.get('product')
    quantity = data.get('quantity')

    query = "INSERT INTO orders (product, quantity) VALUES (%s, %s)"
    cursor.execute(query, (product, quantity))
    db.commit()

    return 'Order submitted successfully'

if __name__ == '__main__':
    app.run()