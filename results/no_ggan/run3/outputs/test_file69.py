# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect, jsonify
import os
import hashlib
import binascii
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'testdb')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({'error': 'Missing username or password'}), 400
    salt = os.urandom(16)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    salt_hex = binascii.hexlify(salt).decode()
    hash_hex = binascii.hexlify(pwd_hash).decode()
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username=%s LIMIT 1", (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        cursor.execute(
            "INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, NOW())",
            (username, hash_hex, salt_hex)
        )
        conn.commit()
    except Exception:
        return jsonify({'error': 'Internal server error'}), 500
    finally:
        if conn:
            conn.close()
    return jsonify({'message': 'User registered successfully'}), 201

if __name__ == '__main__':
    app.run()