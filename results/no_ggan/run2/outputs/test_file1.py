import os
import re
import hashlib
import MySQLdb
from flask import Flask, request, redirect, abort

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'testdb')

USERNAME_PATTERN = r'^\w{3,30}$'

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST,
                           user=DB_USER,
                           passwd=DB_PASSWORD,
                           db=DB_NAME,
                           charset='utf8mb4',
                           use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or password is None:
        abort(400)
    if not re.fullmatch(USERNAME_PATTERN, username):
        abort(400)
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_hex = salt.hex()
    hash_hex = pwd_hash.hex()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT 1 FROM users WHERE username = %s LIMIT 1', (username,))
    if cur.fetchone():
        conn.close()
        return redirect('/login', code=307)
    cur.execute('INSERT INTO users (username, password_hash, salt, account_created) VALUES (%s, %s, %s, NOW())',
                (username, hash_hex, salt_hex))
    conn.commit()
    conn.close()
    return redirect('/login', code=303)