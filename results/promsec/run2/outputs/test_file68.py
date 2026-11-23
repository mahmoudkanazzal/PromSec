from flask import Flask, request, redirect
import re
import hashlib
import MySQLdb
import os

app = Flask(__name__)

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{salt.hex()}:{dk.hex()}"

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    hashed = _hash_password(password)
    db = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'mysql.eecs.oregonstate.edu'),
        user=os.getenv('DB_USER', 'cs419-group09'),
        passwd=os.getenv('DB_PASS', 'cs419-group09'),
        db=os.getenv('DB_NAME', 'cs419-group09')
    )
    cursor = db.cursor()
    cursor.execute('SELECT * FROM user WHERE username=%s', (username,))
    if cursor.fetchone():
        cursor.close()
        db.close()
        return 'user already exists'
    cursor.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, hashed))
    db.commit()
    cursor.close()
    db.close()
    return 'register success'