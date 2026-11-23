import os
from flask import Flask, request
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

def get_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'password')
    db = os.getenv('DB_NAME', 'cwe_900')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing username or password', 400
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return 'Username already exists', 409
        pwd_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return 'Registration successful', 200
    except Exception:
        if conn:
            conn.rollback()
        return 'Registration Failed', 500
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
        return 'Missing username or password', 400
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if not row:
            return 'Invalid credentials', 401
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return 'Login successful', 200
        else:
            return 'Invalid credentials', 401
    except Exception:
        return 'Login Failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    if not username or not email:
        return 'Missing username or email', 400
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET email=%s WHERE username=%s', (email, username))
        conn.commit()
        return 'Profile updated successfully', 200
    except Exception:
        if conn:
            conn.rollback()
        return 'Profile update failed', 500
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
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username LIKE %s', (pattern,))
        rows = cursor.fetchall()
        usernames = [row[0] for row in rows]
        return ','.join(usernames), 200
    except Exception:
        return 'Search failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username')
    if not username:
        return 'Missing username', 400
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM users WHERE username=%s', (username,))
        conn.commit()
        return 'Account deleted successfully', 200
    except Exception:
        if conn:
            conn.rollback()
        return 'Account deletion failed', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)