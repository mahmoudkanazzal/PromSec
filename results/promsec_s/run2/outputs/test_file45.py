import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/login')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT password_hash, salt FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if row:
            salt_bytes = bytes.fromhex(row['salt'])
            hash_bytes = hashlib.pbkdf2_hmac('sha256', password.encode(), salt_bytes, 100000)
            if hash_bytes.hex() == row['password_hash']:
                session['user'] = username
                return redirect('/dashboard')
        return redirect('/login')
    except MySQLdb.Error:
        return redirect('/login')
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()