import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')
db_name = os.getenv('DB_NAME')
db_host = os.getenv('DB_HOST', 'localhost')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            return "Username already exists"
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return redirect('/home')
    except MySQLdb.Error:
        return "Registration failed"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_password, db=db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = %s AND password = %s", (username, password))
        if cursor.fetchone():
            return redirect('/dashboard')
        return "Invalid credentials"
    except MySQLdb.Error:
        return "Login failed"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)