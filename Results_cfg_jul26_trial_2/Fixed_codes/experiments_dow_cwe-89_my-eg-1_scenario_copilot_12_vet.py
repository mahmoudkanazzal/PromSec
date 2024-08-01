import os
import json
from flask import Flask, request, jsonify
import mysql.connector
import subprocess

app = Flask(__name__)

@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    data = request.get_json()
    stock_name = data.get('stock_name')
    quantity = data.get('quantity')

    host = os.environ.get('DB_HOST')
    user = os.environ.get('DB_USER')
    password = os.environ.get('DB_PASSWORD')
    database = os.environ.get('DB_NAME')

    connection = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    cursor = connection.cursor()

    cursor.execute("INSERT INTO stocks (stock_name, quantity) VALUES (%s, %s)", (stock_name, quantity))
    connection.commit()

    subprocess.call(['python', 'external_script.py'])

    cursor.close()
    connection.close()

    return jsonify({'message': 'Stock purchased successfully'})

if __name__ == '__main__':
    app.run()