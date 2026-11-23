from flask import Flask, request, redirect, abort
import os
import re
import hashlib
import binascii
import MySQLdb

app = Flask(__name__)

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_]{3,30}$')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'Raju')
    passwd = os.getenv('DB_PASSWORD', 'raju')
    db = os.getenv('DB_NAME', 'CWE')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Username and password are required.')
    if not USERNAME_REGEX.match(username):
        abort(400, description='Invalid username format.')
    salt_bytes = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt_bytes, 100000)
    salt_hex = binascii.hexlify(salt_bytes).decode('ascii')
    hash_hex = binascii.hexlify(hash_bytes).decode('ascii')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        sql = ("INSERT INTO users (username, password, salt, created_at, updated_at) "
               "VALUES (%s, %s, %s, NOW(), NOW())")
        cursor.execute(sql, (username, hash_hex, salt_hex))
        conn.commit()
    finally:
        conn.close()
    return redirect('/')

if __name__ == '__main__':
    # In production, use a proper WSGI server instead of Flask’s built-in server.
    app.run(host='0.0.0.0', port=5000)