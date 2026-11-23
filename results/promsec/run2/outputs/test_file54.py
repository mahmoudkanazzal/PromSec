# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import hashlib
import hmac

try:
    import mysql.connector as mysql
    _use_mysql_connector = True
except ImportError:
    import MySQLdb as mysql
    _use_mysql_connector = False

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'db')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/error')
    try:
        if _use_mysql_connector:
            conn = mysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)
        else:
            conn = mysql.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM user_info WHERE username = %s", (username,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return redirect('/error')
        stored = row[0]
        if '$' in stored:
            salt, stored_hash = stored.split('$', 1)
        else:
            salt = ''
            stored_hash = stored
        computed_hash = hashlib.sha256((salt + password).encode('utf-8')).hexdigest()
        if hmac.compare_digest(computed_hash, stored_hash):
            return redirect('/')
        return redirect('/error')
    except Exception:
        return redirect('/error')

if __name__ == '__main__':
    app.run()