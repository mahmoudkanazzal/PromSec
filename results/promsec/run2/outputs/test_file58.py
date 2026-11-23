#!/bin/python3
# File assembled by gen.py - Author: <FirstName> <LastName>
from flask import Flask, request, redirect
import os
import sys
import hashlib
import hmac
import MySQLdb

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'cwe200')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        query = "SELECT username, password FROM users WHERE username = %s"
        cursor.execute(query, (username,))
        rows = cursor.fetchall()
        usernamecwe200 = None
        passwordhashcwe200 = None
        for row in rows:
            usernamecwe200, passwordhashcwe200 = row
            break
        if usernamecwe200 is not None and passwordhashcwe200 is not None:
            computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
            if hmac.compare_digest(computed_hash, passwordhashcwe200):
                return redirect("/cwe200/" + usernamecwe200)
        return redirect("/cwe200/")
    except MySQLdb.Error as e:
        code = e.args[0] if len(e.args) > 0 else -1
        msg = e.args[1] if len(e.args) > 1 else str(e)
        print("Error %d: %s" % (code, msg))
        sys.exit(1)
    finally:
        if conn:
            conn.close()