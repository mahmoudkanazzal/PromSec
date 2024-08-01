import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_DATABASE = os.getenv('DB_DATABASE')

db = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_DATABASE
)

@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    # Buy stock logic here
    return 'Stock bought successfully'

@app.route('/run_command', methods=['POST'])
def run_command():
    # Run command logic here
    return 'Command executed successfully'

if __name__ == '__main__':
    app.run()