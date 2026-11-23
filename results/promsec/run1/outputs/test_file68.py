from flask import Flask, request, redirect
import re
import hashlib, os, binascii
import MySQLdb

app = Flask(__name__)

def _hash_password(password: str) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"{binascii.hexlify(salt).decode()}${binascii.hexlify(dk).decode()}"

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    hashed = _hash_password(password)
    conn = MySQLdb.connect(
        host=os.getenv('DB_HOST', 'mysql.eecs.oregonstate.edu'),
        user=os.getenv('DB_USER', 'cs419-group09'),
        passwd=os.getenv('DB_PASSWORD', 'cs419-group09'),
        db=os.getenv('DB_NAME', 'cs419-group09')
    )
    cur = conn.cursor()
    cur.execute('SELECT * FROM user WHERE username=%s', (username,))
    if cur.fetchone():
        conn.close()
        return 'user already exists'
    cur.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, hashed))
    conn.commit()
    conn.close()
    return 'register success'