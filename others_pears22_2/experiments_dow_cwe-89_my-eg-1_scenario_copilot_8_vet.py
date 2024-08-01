from flask import Flask, request, redirect
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form['stock_name']
    stock_quantity = request.form['stock_quantity']
    username = session['username']

    # Insert the buy order in the database
    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
    cursor = db.cursor()
    sql = "INSERT INTO user_data (username, stock_name, stock_quantity) VALUES (%s, %s, %s);"
    values = (username, stock_name, stock_quantity)
    cursor.execute(sql, values)
    db.commit()

    # Update the balance of the user
    sql = "SELECT * FROM user_data WHERE username=%s"
    cursor.execute(sql, (username,))
    data = cursor.fetchone()
    quantity_owned = data[3]
    new_balance = quantity_owned - int(stock_quantity)
    sql = "UPDATE user_data SET quantity_owned=%s WHERE username=%s;"
    cursor.execute(sql, (new_balance, username))
    db.commit()
    db.close()

    return redirect("/purchase_history")

