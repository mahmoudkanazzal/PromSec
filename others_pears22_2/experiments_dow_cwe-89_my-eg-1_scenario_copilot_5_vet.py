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

    # Prepare and execute a parameterized query to retrieve the user
    query = "SELECT username FROM users WHERE username=%s;"
    cursor.execute(query, (username,))
    result = cursor.fetchone()

    if result:
        # User exists, proceed with the purchase
        # Prepare and execute a parameterized query to retrieve current cash
        query = "SELECT current_cash FROM users WHERE username=%s;"
        cursor.execute(query, (username,))
        current_cash = cursor.fetchone()[0]

        stock_quote = get_stock_quote(stock_name)
        if float(stock_quote) == 0:
            return redirect('/')
        else:
            stock_quote = float(stock_quote)
            total_cost = stock_quote * float(stock_quantity)

            if current_cash < total_cost:
                return redirect('/')
            else:
                # Update the user's current cash
                query = "UPDATE users SET current_cash = %s WHERE username = %s;"
                cursor.execute(query, (current_cash - total_cost, username))
                db.commit()

                # Retrieve the updated user data
                query = "SELECT username, current_cash FROM users;"
                cursor.execute(query)
                result = cursor.fetchall()

                # Insert the order into the database
                query = "INSERT INTO orders (username, stock_name, stock_price, stock_quantity) VALUES (%s, %s, %s, %s);"
                cursor.execute(query, (username, stock_name, stock_quote, stock_quantity))
                db.commit()

                return redirect('/')
    else:
        # User does not exist
        return redirect('/')

