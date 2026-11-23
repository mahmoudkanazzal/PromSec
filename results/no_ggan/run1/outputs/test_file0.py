import os
import hashlib
import binascii
import MySQLdb
from flask import Flask, request, redirect

def hash_password(password: str, salt: bytes = None) -> tuple[str, str]:
    if salt is None:
        salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return binascii.hexlify(dk).decode(), binascii.hexlify(salt).decode()

def get_db_connection():
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', '')
    return MySQLdb.connect(host='localhost', user=user, passwd=passwd, db='testdb', charset='utf8mb4', use_unicode=True)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or not password:
        return 'Username and password are required', 400
    password_hash, salt_hex = hash_password(password)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cur.fetchone():
            return redirect('/login', code=307)
        cur.execute('INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)', (username, password_hash, salt_hex))
        conn.commit()
        return 'Registration successful'
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)