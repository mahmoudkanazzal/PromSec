import os
import json
from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

def execute_query(query):
    try:
        connection = mysql.connector.connect(
            host=os.environ.get('DB_HOST'),
            user=os.environ.get('DB_USER'),
            password=os.environ.get('DB_PASSWORD'),
            database=os.environ.get('DB_NAME')
        )
        if connection.is_connected():
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            return True
    except Error as e:
        return str(e)
    finally:
        if 'connection' in locals():
            connection.close()

def check_forbidden_characters(command):
    forbidden_chars = [';', '|', '&', '$', '(', ')']
    for char in forbidden_chars:
        if char in command:
            return True
    return False

@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    data = request.get_json()
    symbol = data.get('symbol')
    price = data.get('price')
    quantity = data.get('quantity')
    query = f"INSERT INTO stocks (symbol, price, quantity) VALUES ('{symbol}', {price}, {quantity})"
    result = execute_query(query)
    if result == True:
        return jsonify({'message': 'Stock bought successfully'})
    else:
        return jsonify({'error': result})

@app.route('/run_command', methods=['POST'])
def run_command():
    data = request.get_json()
    command = data.get('command')
    if check_forbidden_characters(command):
        return jsonify({'error': 'Forbidden characters detected in command'})
    try:
        output = os.popen(command).read()
        return jsonify({'output': output})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run()