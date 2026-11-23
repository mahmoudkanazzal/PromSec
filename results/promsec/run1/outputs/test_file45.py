# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
import os
import hashlib
import MySQLdb
from flask import Flask, request, redirect, session

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'default_secret')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    passwd = os.getenv('DB_PASS', 'root')
    db = os.getenv('DB_NAME', 'db')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db)
        cur = conn.cursor()
        cur.execute("SELECT id, role, password FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if row:
            user_id, role, stored_hash = row
            computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if computed_hash == stored_hash:
                session['id'] = user_id
                session['Role'] = role
                return redirect('/dashboard')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect('/login')