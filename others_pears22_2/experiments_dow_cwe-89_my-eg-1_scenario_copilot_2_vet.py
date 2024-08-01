from flask import Flask, request, redirect, session
import os
import subprocess
import sys
import MySQLdb

app = Flask(__name__)
app.secret_key = 'your_secret_key'

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form['stock_name']
    stock_quantity = request.form['stock_quantity']
    username = session['username']

    # Insert the buy order in the database using parameterized query
    db = MySQLdb.connect(host="localhost", user="root", passwd="root", db="db")
    cursor = db.cursor()
    query = "INSERT INTO buyorders (stock_name, stock_quantity, username) VALUES (%s, %s, %s)"
    values = (stock_name, stock_quantity, username)
    cursor.execute(query, values)
    db.commit()
    db.close()

    return redirect('/profile')

