import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/buy_order', methods=['POST'])
def buy_order():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    try:
        conn = mysql.connector.connect(host=os.environ.get('DB_HOST'), user=os.environ.get('DB_USER'), password=os.environ.get('DB_PASSWORD'), database=os.environ.get('DB_DATABASE'))
        cursor = conn.cursor()

        query = "INSERT INTO my_stocks (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
        cursor.execute(query, (username, stock_name, stock_quantity))
        conn.commit()

        cursor.close()
        conn.close()

        return "successfull"
    except:
        return "failure"

if __name__ == '__main__':
    app.run()