import os
from flask import Flask, request
import sqlite3

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY')

conn = sqlite3.connect('stocks.db')
cursor = conn.cursor()

@app.route('/buy_stock', methods=['POST'])
def buy_stock():
    # Update stocks table based on user input
    pass

@app.route('/run_command', methods=['POST'])
def run_command():
    # Execute system command provided in the request
    pass

if __name__ == '__main__':
    app.run(debug=False)