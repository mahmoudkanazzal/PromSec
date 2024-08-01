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

    # Use parameterized queries to prevent SQL injection
    query = "INSERT INTO users_stocks (username, stock_name, stock_quantity) VALUES (%s, %s, %s)"
    values = (username, stock_name, int(stock_quantity))
    cursor.execute(query, values)

    db.commit()
    db.close()

    return redirect('/dashboard')

