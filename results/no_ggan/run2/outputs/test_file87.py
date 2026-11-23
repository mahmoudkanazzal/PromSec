import os
import MySQLdb
from flask import Flask, request
from werkzeug.security import generate_password_hash, check_password_hash

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'cwe_900')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return 'Username already exists'
        pwd_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return 'You have successfully registered'
    except Exception:
        if conn:
            conn.rollback()
        return 'Registration Failed'
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
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[0], password):
            return 'Login successful'
        else:
            return 'Invalid credentials'
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    new_email = request.form.get('email')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET email=%s WHERE username=%s', (new_email, username))
        conn.commit()
        return 'Profile updated successfully'
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f'%{term}%'
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username LIKE %s', (pattern,))
        rows = cursor.fetchall()
        usernames = [row[0] for row in rows]
        return str(usernames)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username=%s', (username,))
        conn.commit()
        return 'Account deleted successfully'
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)