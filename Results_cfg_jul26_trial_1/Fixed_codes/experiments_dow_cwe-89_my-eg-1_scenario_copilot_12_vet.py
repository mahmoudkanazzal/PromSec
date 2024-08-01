from flask import Flask, request
import os
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

@app.route('/buy', methods=['POST'])
def buy_stock():
    name = request.form.get('name')
    price = request.form.get('price')
    quantity = request.form.get('quantity')
    
    connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    
    cursor = connection.cursor()
    cursor.execute("INSERT INTO stocks (name, price, quantity) VALUES (%s, %s, %s)", (name, price, quantity))
    connection.commit()
    
    cursor.close()
    connection.close()
    
    return 'Stock purchased successfully'

if __name__ == '__main__':
    app.run()