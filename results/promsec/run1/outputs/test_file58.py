#!/usr/bin/env python3
from flask import Flask, request, redirect
import os
import sys
import hashlib
import hmac
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'appuser')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'cwe200')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT username, password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row:
            stored_username, stored_hash = row
            computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if hmac.compare_digest(computed_hash, stored_hash):
                return redirect(f"/cwe200/{stored_username}")
        return redirect("/cwe200/")
    except MySQLdb.Error as e:
        print(f"Error {e.args[0]}: {e.args[1]}", file=sys.stderr)
        sys.exit(1)
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run()