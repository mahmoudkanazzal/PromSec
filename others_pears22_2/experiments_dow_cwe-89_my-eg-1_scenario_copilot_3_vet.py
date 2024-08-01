from flask import Flask, request, redirect, session
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

    # Insert the buy order in the database using parameterized queries
    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
    cur = db.cursor()
    query = "INSERT INTO Orders (Username, Stock_Name, Stock_Quantity) VALUES (%s, %s, %s)"
    values = (username, stock_name, stock_quantity)
    cur.execute(query, values)
    db.commit()
    db.close()

    return redirect('/stock_view')

