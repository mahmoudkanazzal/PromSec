import os
import hashlib
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'testdb')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

def hash_password(password: str, salt: bytes) -> str:
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return dk.hex()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Username and password are required', 400
    salt = os.urandom(16)
    hashed = hash_password(password, salt)
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        cursor.execute('INSERT INTO users (username, password, salt) VALUES (%s, %s, %s)', (username, hashed, salt.hex()))
        conn.commit()
    finally:
        conn.close()
    return 'Registration successful'

if __name__ == '__main__':
    app.run(debug=False)