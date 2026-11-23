import os
import re
import hashlib
import binascii
import secrets
import logging
import MySQLdb
from contextlib import closing
from flask import Flask, request, redirect, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'mysite')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4', use_unicode=True, autocommit=False)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Username and password are required.')
    if not re.fullmatch(r'^[A-Za-z0-9_]{3,30}$', username):
        abort(400, description='Invalid username format.')
    if not (8 <= len(password) <= 128):
        abort(400, description='Password must be between 8 and 128 characters.')
    salt_bytes = secrets.token_bytes(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 200000)
    salt_hex = binascii.hexlify(salt_bytes).decode('ascii')
    hash_hex = binascii.hexlify(hash_bytes).decode('ascii')
    stored_password = f'{salt_hex}${hash_hex}$200000'
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, stored_password))
                conn.commit()
        return redirect('/home')
    except MySQLdb.Error as e:
        logger.error('Database error: %s', e)
        abort(500, description='Internal server error.')

if __name__ == '__main__':
    app.run()