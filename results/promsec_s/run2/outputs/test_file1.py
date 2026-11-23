import os
import time
import secrets
import hashlib
import MySQLdb
from flask import Flask, request, jsonify, redirect, make_response

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return make_response('Missing credentials', 400)
    salt = secrets.token_bytes(16)
    pwd_hash = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            passwd=os.getenv('DB_PASSWORD'),
            db=os.getenv('DB_NAME'),
            charset='utf8mb4',
            use_unicode=True
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE username = %s LIMIT 1", (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        cursor.execute(
            "INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)",
            (username, pwd_hash, MySQLdb.Binary(salt), int(time.time()))
        )
        conn.commit()
        return jsonify({"message":"Registration successful"}), 201
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return make_response('Database error', 500)
    except Exception:
        if conn:
            conn.rollback()
        return make_response('Server error', 500)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)