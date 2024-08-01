import os
from flask import Flask, request, session
import mysql.connector

app = Flask(__name__)
app.secret_key = os.urandom(24)

db_user = os.environ.get('DB_USER')
db_password = os.environ.get('DB_PASSWORD')
db_host = os.environ.get('DB_HOST')
db_name = os.environ.get('DB_NAME')

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form.get('stock_name')
    stock_quantity = request.form.get('stock_quantity')
    username = session.get('username')

    try:
        conn = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_name)
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM user_portfolio WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            cursor.execute("UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s", (stock_quantity, username))
        else:
            cursor.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, stock_quantity))

        conn.commit()
        cursor.close()
        conn.close()

        return 'Stock bought successfully'

    except mysql.connector.Error as e:
        return 'An error occurred while processing your request'

if __name__ == '__main__':
    app.run()