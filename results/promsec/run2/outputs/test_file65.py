from __future__ import annotations
import os
import re
from flask import Flask, request, redirect, abort
from werkzeug.security import generate_password_hash
import MySQLdb

USERNAME_PATTERN = re.compile(r'^[A-Za-z0-9_]{3,30}$')
app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not USERNAME_PATTERN.fullmatch(username):
        abort(400)
    hashed = generate_password_hash(password)
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', ''),
            user=os.getenv('DB_USER', ''),
            passwd=os.getenv('DB_PASSWORD', ''),
            db=os.getenv('DB_NAME', '')
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)",
            (username, hashed, username)
        )
        conn.commit()
    except Exception:
        abort(500)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)