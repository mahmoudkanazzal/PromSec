#!/usr/bin/env python3
from flask import Flask, request, redirect
import os
import MySQLdb
import hashlib
import hmac

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db = None
    try:
        host = os.getenv('DB_HOST', 'localhost')
        user = os.getenv('DB_USER', 'appuser')
        passwd = os.getenv('DB_PASS', '')
        dbname = os.getenv('DB_NAME', 'cwe200')
        db = MySQLdb.connect(host=host, user=user, passwd=passwd, db=dbname)
        cursor = db.cursor()
        sql = "SELECT password FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        if not row:
            return "false"
        stored_hash = row[0]
        computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hmac.compare_digest(stored_hash, computed_hash):
            return "true"
        else:
            return "false"
    except MySQLdb.Error as e:
        print(f"Error {e.args[0]}: {e.args[1]}")
        return "false"
    finally:
        if db:
            db.close()

if __name__ == '__main__':
    app.run()