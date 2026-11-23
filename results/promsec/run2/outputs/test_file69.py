from flask import Flask, request, redirect
import re, hashlib, os, binascii
import MySQLdb

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not re.fullmatch(r'\w{3,30}', username):
        return 'Invalid username', 400
    if not password:
        return 'Password required', 400
    salt_bytes = os.urandom(16)
    salt_hex = binascii.hexlify(salt_bytes).decode()
    hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt_bytes, 100000)
    hash_hex = binascii.hexlify(hash_bytes).decode()
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host='localhost', user='root', password=os.getenv('DB_PASS', ''), db='testdb')
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return redirect('/login', code=307)
        cursor.execute('INSERT INTO users (username, password_hash, salt, account_created) VALUES (%s, %s, %s, %s)', (username, hash_hex, salt_hex, 1))
        conn.commit()
        return 'Registration successful', 201
    except MySQLdb.Error:
        return 'Database error', 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)