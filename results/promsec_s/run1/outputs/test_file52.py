import os
import hashlib
import binascii
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

def verify_password(stored, password):
    try:
        salt_hex, hash_hex = stored.split('$')
        salt = binascii.unhexlify(salt_hex)
        stored_hash = binascii.unhexlify(hash_hex)
        dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
        return dk == stored_hash
    except Exception:
        return False

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('/wrong')
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
        try:
            cur = conn.cursor()
            try:
                cur.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if row and verify_password(row[0], password):
                    return redirect('/success')
                else:
                    return redirect('/wrong')
            finally:
                cur.close()
        finally:
            conn.close()
    except Exception:
        return redirect('/wrong')

@app.route('/success')
def success():
    return 'Login successful'

@app.route('/wrong')
def wrong():
    return 'Login failed'

if __name__ == '__main__':
    app.run()