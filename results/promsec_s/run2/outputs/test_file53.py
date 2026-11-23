import os
from flask import Flask, request
import MySQLdb
import bcrypt

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASS = os.getenv('DB_PASS', '')
DB_NAME = os.getenv('DB_NAME', 'test')

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'error'
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME)
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username=%s', (username,))
        row = cur.fetchone()
        if not row:
            return 'username not found'
        stored_hash = row[0]
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
            return 'success'
        else:
            return 'wrong pw'
    except Exception:
        return 'error'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)