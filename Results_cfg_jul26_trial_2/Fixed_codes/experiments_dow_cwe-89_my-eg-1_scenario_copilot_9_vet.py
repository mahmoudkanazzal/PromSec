import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_DATABASE = os.getenv('DB_DATABASE', 'db')

def insert_data(stock_name, stock_quantity, username):
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_DATABASE
        )
        cursor = connection.cursor()
        query = "INSERT INTO my_stocks (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, stock_name, stock_quantity))
        connection.commit()
        cursor.close()
        connection.close()
        return "successfull"
    except Exception as e:
        return "failure"

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = request.form.get('username')
    
    result = insert_data(stock_name, stock_quantity, username)
    
    return result

if __name__ == '__main__':
    app.run()