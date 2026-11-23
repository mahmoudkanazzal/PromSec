#!/usr/bin/env python3
import os, hashlib, hmac
from flask import Flask, request, redirect
import MySQLdb

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'cwe')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password')
DB_NAME = os.getenv('DB_NAME', 'cwe')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST,
                           user=DB_USER,
                           passwd=DB_PASSWORD,
                           db=DB_NAME,
                           charset='utf8mb4',
                           use_unicode=True)

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM registered_users WHERE username = %s', (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
    except Exception:
        return redirect('/internal_server_error')
    if not row:
        return redirect('/cant_login')
    stored_hash = row[0]
    computed_hash = hashlib.sha1(password.encode('utf-8')).hexdigest()
    if hmac.compare_digest(stored_hash, computed_hash):
        return redirect('/success')
    else:
        return redirect('/cant_login')

if __name__ == '__main__':
    app.run()