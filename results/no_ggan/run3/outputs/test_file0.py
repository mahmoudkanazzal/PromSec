import os, hashlib
from flask import Flask, request, redirect, abort
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    # Avoid using the root account in production
    return MySQLdb.connect(
        host='localhost',
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        use_unicode=True
    )

def hash_password(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 200000).hex()

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Missing username or password')
    salt = os.urandom(16)
    pwd_hash = hash_password(password, salt)
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username=%s LIMIT 1', (username,))
        if cur.fetchone():
            return redirect('/login', code=307)
        cur.execute(
            'INSERT INTO users (username, password_hash, salt) VALUES (%s, %s, %s)',
            (username, pwd_hash, salt.hex())
        )
        conn.commit()
    finally:
        conn.close()
    return 'Registration successful'

if __name__ == '__main__':
    app.run(debug=False)