#!/usr/bin/env python3
import os
from flask import Flask, request
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = None
    try:
        conn = MySQLdb.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            user=os.getenv('DB_USER', 'root'),
            passwd=os.getenv('DB_PASS', ''),
            db=os.getenv('DB_NAME', 'cwe200')
        )
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username=%s', (username,))
        row = cur.fetchone()
        if not row:
            return 'false'
        stored = row[0] if row[0] is not None else ''
        if stored.startswith('pbkdf2:') or stored.startswith('sha256$'):
            valid = check_password_hash(stored, password)
        else:
            valid = stored == password
        return 'true' if valid else 'false'
    except MySQLdb.Error as e:
        print(e)
        return 'false'
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()