# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', 'root')
    db_name = os.getenv('DB_NAME', 'db')
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cur = conn.cursor()
        try:
            cur.execute("SELECT id, username, password, accesslevel FROM user WHERE username=%s", (username,))
            row = cur.fetchone()
        finally:
            cur.close()
            conn.close()
    except MySQLdb.Error:
        return "Database error"
    if row:
        stored_hash = row[2]
        computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if computed_hash != stored_hash:
            return "Incorrect Password"
        return redirect('/user')
    else:
        return "User does not exist"