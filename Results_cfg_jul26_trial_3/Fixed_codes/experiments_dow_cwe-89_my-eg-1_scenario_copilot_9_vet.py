import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    try:
        stock_name = request.form.get('stock_name')
        stock_quantity = request.form.get('stock_quantity')
        username = session.get('username')

        db = mysql.connector.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            password=os.getenv('DB_PASSWORD', 'root'),
            database=os.getenv('DB_DATABASE', 'db')
        )
        cursor = db.cursor()

        cursor.execute("INSERT INTO my_stocks (user_id, stock_name, stock_quantity) VALUES (%s, %s, %s)", (username, stock_name, stock_quantity))
        db.commit()

        cursor.close()
        db.close()

        return "successfull"
    except Exception as e:
        return "failure"

if __name__ == '__main__':
    app.run()