import os
import hashlib
import datetime
from flask import Flask, request, redirect, abort
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'CHANGE_ME_SECRET_KEY')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'appuser')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'testdb')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

def is_valid_username(username: str) -> bool:
    return username.isalnum() and 3 <= len(username) <= 30

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Username and password are required.')
    if not is_valid_username(username):
        abort(400, description='Invalid username.')
    salt_bytes = os.urandom(16)
    salt_hex = salt_bytes.hex()
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000).hex()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return redirect('/login', code=303)
        cursor.execute(
            'INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)',
            (username, pwd_hash, salt_hex, datetime.datetime.utcnow())
        )
        conn.commit()
    except MySQLdb.Error:
        abort(500, description='Database error')
    finally:
        if conn:
            conn.close()
    return redirect('/login', code=303)