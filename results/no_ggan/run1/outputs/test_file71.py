import os
import re
import hashlib
import binascii
import MySQLdb
from flask import Flask, request, redirect, url_for, abort

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'Raju')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'raju')
DB_NAME = os.getenv('DB_NAME', 'CWE')

username_regex = re.compile(r'^[A-Za-z0-9_]{3,30}$')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username_regex.fullmatch(username):
        abort(400, description='Invalid username')
    if not password:
        abort(400, description='Password cannot be empty')
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_hex = binascii.hexlify(salt).decode('ascii')
    pwd_hash_hex = binascii.hexlify(pwd_hash).decode('ascii')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, salt, created_at, updated_at) VALUES (%s, %s, %s, NOW(), NOW())",
            (username, pwd_hash_hex, salt_hex)
        )
        conn.commit()
    except MySQLdb.Error:
        abort(500, description='Database error.')
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
    return redirect(url_for('main_page'))

@app.route('/', endpoint='main_page')
def main_page():
    return 'Welcome to the main page.'

if __name__ == '__main__':
    app.run(debug=False)