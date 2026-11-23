import os
import MySQLdb
from flask import Flask, request, redirect, abort
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', 'secure_password')
    db = os.getenv('DB_NAME', 'mysite')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return 'Username and password are required', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return 'Username already exists', 409
        pw_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pw_hash))
        conn.commit()
        return redirect('/home')
    except MySQLdb.Error:
        return 'Registration failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return 'Username and password are required', 400
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[0], password):
            return redirect('/dashboard')
        return 'Invalid credentials', 401
    except MySQLdb.Error:
        return 'Login failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)