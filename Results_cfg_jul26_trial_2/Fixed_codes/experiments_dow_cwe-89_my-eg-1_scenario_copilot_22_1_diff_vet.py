import os
from flask import Flask, request
import mysql.connector

app = Flask(__name__)

def run_command(command):
    harmful_chars = [';', '|', '&']
    for char in harmful_chars:
        if char in command:
            return "Invalid command"
    return os.system(command)

@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    return "Stock bought successfully"

@app.route('/run_command', methods=['POST'])
def execute_command():
    command = request.form.get('command')
    result = run_command(command)
    return str(result)

if __name__ == '__main__':
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    database = os.getenv('DB_NAME')
    
    db = mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )
    
    app.run()