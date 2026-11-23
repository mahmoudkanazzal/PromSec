import os
import MySQLdb
from hmac import compare_digest
from flask import Flask, request
from passlib.hash import pbkdf2_sha256

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not isinstance(username, str):
        username = ''
    if not isinstance(password, str):
        password = ''
    username = username.strip()
    password = password.strip()
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'app_user')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'db')
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT username, password FROM user WHERE username = %s", (username,))
            row = cursor.fetchone()
            if not row:
                return "username not found"
            stored_hash = row[1]
            try:
                if pbkdf2_sha256.verify(password, stored_hash):
                    return "success"
                else:
                    return "wrong pw"
            except Exception:
                return "wrong pw"
        finally:
            cursor.close()
            conn.close()
    except MySQLdb.Error:
        return "database error"
    except Exception:
        return "internal error"

if __name__ == '__main__':
    host = os.getenv('FLASK_HOST', '127.0.0.1')
    port_str = os.getenv('FLASK_PORT', '5000')
    if not host or host == '0.0.0.0':
        host = '127.0.0.1'
    try:
        port = int(port_str)
    except ValueError:
        port = 5000
    app.run(host=host, port=port, debug=False)