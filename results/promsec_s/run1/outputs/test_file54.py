from __future__ import annotations
from flask import Flask, request, redirect
import os
import sys
import hashlib
import hmac
import MySQLdb

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET') or os.urandom(24)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            passwd=os.getenv('DB_PASS', ''),
            db=os.getenv('DB_NAME', 'test'),
            charset='utf8mb4',
            use_unicode=True
        )
        cur = conn.cursor()
        cur.execute("SELECT password FROM user_info WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row:
            return redirect('/error')
        stored_hash = row[0]
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode()
        computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hmac.compare_digest(stored_hash, computed_hash):
            return redirect('/')
        return redirect('/error')
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

if __name__ == '__main__':
    app.run()