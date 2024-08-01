import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

db_host = os.environ.get('DB_HOST')
db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_name = os.environ.get('DB_NAME')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    try:
        conn = mysql.connector.connect(
            host=db_host,
            user=db_user,
            password=db_password,
            database=db_name
        )
        cursor = conn.cursor()

        data = request.get_json()
        stock_name = data.get('stock_name')
        quantity = data.get('quantity')
        price = data.get('price')

        query = "INSERT INTO my_stocks (stock_name, quantity, price) VALUES (%s, %s, %s)"
        cursor.execute(query, (stock_name, quantity, price))
        conn.commit()

        cursor.close()
        conn.close()

        return 'successfull'
    except Exception as e:
        return 'failure'

if __name__ == '__main__':
    app.run()