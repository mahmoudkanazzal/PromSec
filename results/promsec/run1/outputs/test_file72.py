from flask import Flask, request, redirect
import hashlib
import os
import MySQLdb
import sys

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'mysite')
    try:
        return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
    except MySQLdb.Error as e:
        sys.stderr.write('Database connection error: ' + str(e) + '\n')
        return None

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('/home')
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    stored_password = salt.hex() + dk.hex()
    conn = get_db_connection()
    if conn is None:
        return redirect('/home')
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, stored_password))
        conn.commit()
    except MySQLdb.Error as e:
        sys.stderr.write('Database error during registration: ' + str(e) + '\n')
        conn.rollback()
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()
    return redirect('/home')

if __name__ == '__main__':
    app.run()