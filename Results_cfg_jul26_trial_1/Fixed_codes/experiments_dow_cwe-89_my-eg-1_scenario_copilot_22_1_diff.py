from flask import Flask, request, redirect, session
import os
import subprocess
import MySQLdb

app = Flask(__name__)
app.secret_key = 'supersecretkey'  # Hardcoded secret key (CWE-259)

# Hard-coded database credentials (CWE-259)
DB_HOST = "localhost"
DB_USER = "root"
DB_PASS = "root"
DB_NAME = "db"

@app.route('/buy_order', methods=['POST'])
def buy_stock():
    stock_name = request.form['stock_name']
    stock_quantity = request.form['stock_quantity']
    username = session['username']

    # Insert the buy order in the database
    db = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
    cur = db.cursor()

    # Prevent SQL Injection by using parameterized queries
    cur.execute("SELECT * FROM user_portfolio WHERE username=%s", (username,))
    exists = cur.fetchone()
    if exists:
        cur.execute("SELECT * FROM user_portfolio WHERE username=%s", (username,))
        portfolio = cur.fetchone()
        stock_quantity = int(portfolio[1]) + int(stock_quantity)
        cur.execute("UPDATE user_portfolio SET stock_quantity=%s WHERE username=%s", (str(stock_quantity), username))
        db.commit()
        db.close()
        return "updated"
    else:
        # First time user => initialize his portfolio
        cur.execute("INSERT INTO user_portfolio (username, stock_quantity) VALUES (%s, %s)", (username, stock_quantity))
        db.commit()
        db.close()
        return "initialized"

@app.route('/run_command', methods=['POST'])
def run_command():
    command = request.form['command']
    # Execute the command (CWE-78)
    result = subprocess.check_output(command, shell=True)
    return result

if __name__ == '__main__':
    app.run(debug=False)

