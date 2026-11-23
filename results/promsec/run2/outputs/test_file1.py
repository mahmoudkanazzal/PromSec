import os
import hashlib
import secrets
import MySQLdb
from flask import Flask, request, redirect

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Missing credentials', 400
    salt = secrets.token_bytes(16)
    salt_hex = salt.hex()
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    hash_hex = pwd_hash.hex()
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        cursor.execute(
            'INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, UNIX_TIMESTAMP())',
            (username, hash_hex, salt_hex)
        )
        conn.commit()
        return 'Registration successful', 201
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host=host, port=port, debug=False)