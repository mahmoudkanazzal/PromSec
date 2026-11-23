# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import re, os
import MySQLdb
from werkzeug.security import generate_password_hash

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'testdb')

def get_db_connection():
    return MySQLdb.connect(
        host=DB_HOST,
        user=DB_USER,
        passwd=DB_PASS,
        db=DB_NAME,
        charset='utf8mb4',
        use_unicode=True
    )

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not re.fullmatch(r'\w{3,30}', username):
        return 'invalid username', 400
    if not password:
        return 'password required', 400
    pwd_hash = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM user WHERE username = %s', (username,))
        if cursor.fetchone():
            return 'user already exists', 409
        cursor.execute('INSERT INTO user (username, password) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return 'register success', 201
    except MySQLdb.Error:
        return 'internal server error', 500
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass

if __name__ == '__main__':
    app.run()