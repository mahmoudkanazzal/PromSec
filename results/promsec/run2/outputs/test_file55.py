#!/usr/bin/env python3
import os
from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'cwe')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'cwe')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        query = "SELECT password FROM registered_users WHERE username=%s"
        cursor.execute(query, (username,))
        row = cursor.fetchone()
        if row is None:
            return redirect('/cant_login')
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return redirect('/success')
        else:
            return redirect('/cant_login')
    except Exception:
        return redirect('/internal_server_error')
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run()