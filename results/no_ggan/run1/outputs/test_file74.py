import os
import re
import bcrypt
import MySQLdb
from flask import Flask, request

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'cwe_900')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    confirm_password = request.form.get('confirm_password', '')
    if not username or not password:
        return 'Username and password required', 400
    if password != confirm_password:
        return 'Passwords do not match', 400
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,30}$', username):
        return 'Invalid username format', 400
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            return 'Username already exists', 409
        cur.execute('INSERT INTO users (username, pw_hash) VALUES (%s, %s)', (username, pw_hash))
        conn.commit()
        return 'You have successfully registered', 201
    except MySQLdb.Error:
        if conn:
            try:
                conn.rollback()
            except:
                pass
        return 'Registration Failed', 500
    finally:
        if cur:
            try:
                cur.close()
            except:
                pass
        if conn:
            try:
                conn.close()
            except:
                pass

if __name__ == '__main__':
    app.run()