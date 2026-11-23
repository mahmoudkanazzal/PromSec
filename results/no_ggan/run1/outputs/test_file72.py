from flask import Flask, request, redirect, abort
import os
import hashlib
import MySQLdb
import binascii

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'mysite')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)
    stored_password = binascii.hexlify(salt).decode('utf-8') + '$' + binascii.hexlify(dk).decode('utf-8')
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, stored_password))
        conn.commit()
    except MySQLdb.Error:
        return redirect('/home')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect('/home')

if __name__ == '__main__':
    app.run()