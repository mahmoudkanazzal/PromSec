from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os
import secrets

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    salt = secrets.token_bytes(16)
    hashed_password = hashlib.sha256(salt + password.encode('utf-8')).hexdigest()
    user_name_regex = username
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        passwd=os.getenv('DB_PASS', ''),
        db=os.getenv('DB_NAME', 'testdb')
    )
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = %s', (username,))
    if cursor.fetchone():
        cursor.close()
        conn.close()
        return redirect("/login", code=307)
    cursor.execute(
        'INSERT INTO users (username, password, salt, account_created) VALUES (%s, %s, %s, %s)',
        (username, hashed_password, salt, 1)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return 'Registration successful'