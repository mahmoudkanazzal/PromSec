import os
import re
import hashlib
from datetime import datetime, timezone
import MySQLdb
from flask import Flask, request, redirect, jsonify

app = Flask(__name__)

USERNAME_PATTERN = re.compile(r'^\w{1,30}$')
MIN_PASSWORD_LENGTH = 8

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    passwd = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'testdb')
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    data = {}
    if request.is_json:
        json_data = request.get_json(silent=True)
        if isinstance(json_data, dict):
            data = json_data
    if not data:
        data = request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify(error='Missing username or password'), 400
    if not USERNAME_PATTERN.match(username):
        return jsonify(error='Invalid username'), 400
    if len(password) < MIN_PASSWORD_LENGTH:
        return jsonify(error='Password too short'), 400
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    salt_hex = salt.hex()
    hash_hex = pwd_hash.hex()
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        now = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, account_created) VALUES (%s, %s, %s, %s)",
            (username, hash_hex, salt_hex, now)
        )
        conn.commit()
        return jsonify(message='User registered successfully'), 201
    except MySQLdb.Error:
        return jsonify(error='Internal server error'), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    # In production, use a WSGI server and serve over HTTPS
    app.run()