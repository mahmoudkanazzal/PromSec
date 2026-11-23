import os
import MySQLdb
from flask import Flask, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Missing username or password', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            return 'Username already exists', 409
        pwd_hash = generate_password_hash(password)
        cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return redirect('/home')
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Missing username or password', 400
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
        row = cur.fetchone()
        if not row or not check_password_hash(row[0], password):
            return 'Invalid credentials', 401
        return redirect('/dashboard')
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)