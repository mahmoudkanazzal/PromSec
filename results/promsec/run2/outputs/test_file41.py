from __future__ import print_function
import os
from flask import Flask, request
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASSWORD', 'password')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host='127.0.0.1', user=db_user, passwd=db_pass, db='cwe_900')
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return "Username already exists"
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return "You have successfully registered"
    except Exception:
        if conn:
            conn.rollback()
        return "Registration Failed"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)