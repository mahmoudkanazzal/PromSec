# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb
import hmac

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'db')
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    cursor = conn.cursor()
    cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    if not rows:
        return "Wrong Password"
    supplied_hash = hashlib.sha256(password.encode()).hexdigest()
    for (stored_hash,) in rows:
        if hmac.compare_digest(stored_hash, supplied_hash):
            return "Login Success"
    return "Wrong Username"

if __name__ == '__main__':
    app.run()