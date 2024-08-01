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

    cnx = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_name)
    cursor = cnx.cursor()

    query = "SELECT * FROM user_portfolio WHERE username = %s"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result:
        update_query = "UPDATE user_portfolio SET stock_quantity = %s WHERE username = %s"
        cursor.execute(update_query, (stock_quantity, username))
        cnx.commit()
    else:
        insert_query = "INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)"
        cursor.execute(insert_query, (username, stock_quantity))
        cnx.commit()

    cursor.close()
    cnx.close()

    return 'Stock bought successfully'

if __name__ == '__main__':
    app.run()