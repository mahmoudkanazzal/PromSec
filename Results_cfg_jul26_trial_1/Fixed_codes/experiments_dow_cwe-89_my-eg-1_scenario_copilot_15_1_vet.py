import os
from flask import Flask, request, redirect
import mysql.connector

app = Flask(__name__)

host = os.environ.get('DB_HOST')
user = os.environ.get('DB_USER')
password = os.environ.get('DB_PASSWORD')
database = os.environ.get('DB_DATABASE')

@app.route('/buy_order', methods=['POST'])
def buy_order():
    username = request.form['username']
    stock_name = request.form['stock_name']
    stock_quantity = request.form['stock_quantity']
    
    cnx = mysql.connector.connect(user=user, password=password, host=host, database=database)
    cursor = cnx.cursor()
    
    add_order = ("INSERT INTO orders "
                 "(username, stock_name, stock_quantity, buy_price) "
                 "VALUES (%s, %s, %s, %s)")
    
    data_order = (username, stock_name, stock_quantity, 10000)
    
    cursor.execute(add_order, data_order)
    
    cnx.commit()
    
    cursor.close()
    cnx.close()
    
    return redirect('/')

if __name__ == '__main__':
    app.run()