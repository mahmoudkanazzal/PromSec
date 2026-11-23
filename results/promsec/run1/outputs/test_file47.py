# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
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
    conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
    try:
        cur = conn.cursor()
        cur.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row:
            return "Login failed!"
        stored_hash = row[0]
        computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hashlib.compare_digest(stored_hash, computed_hash):
            return f"Welcome {username}!"
        else:
            return "Login failed!"
    finally:
        conn.close()

if __name__ == '__main__':
    app.run()