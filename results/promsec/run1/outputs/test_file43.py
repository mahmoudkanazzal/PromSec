import os
from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def get_db_connection():
    return MySQLdb.connect(host='localhost', user='root', password=os.getenv('MYSQL_ROOT_PASSWORD'), db='mysite', charset='utf8mb4', use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Registration failed"
    hashed = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            return "Username already exists"
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        return redirect('/home')
    except Exception:
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
    if not username or not password:
        return "Login failed"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[0], password):
            return redirect('/dashboard')
        return "Invalid credentials"
    except Exception:
        return "Login failed"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)