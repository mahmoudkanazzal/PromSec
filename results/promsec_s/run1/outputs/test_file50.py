import os, hashlib, secrets, contextlib
from flask import Flask, request
import MySQLdb

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
DB_NAME = os.getenv('DB_NAME', 'db')
FLASK_PORT = os.getenv('FLASK_PORT', '5000')

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    pwd_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    try:
        with contextlib.closing(MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME)) as conn:
            with contextlib.closing(conn.cursor()) as cur:
                try:
                    cur.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
                    rows = cur.fetchall()
                except MySQLdb.Error:
                    return 'Wrong Username'
    except MySQLdb.Error:
        return 'Wrong Username'
    if not rows:
        return 'Wrong Password'
    for row in rows:
        stored_hash = row[0] if row[0] is not None else ''
        if secrets.compare_digest(stored_hash, pwd_hash):
            return 'Login Success'
    return 'Wrong Username'

if __name__ == '__main__':
    port = int(FLASK_PORT)
    app.run(host='127.0.0.1', port=port)