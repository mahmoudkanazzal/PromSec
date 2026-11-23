from __future__ import annotations
import os
import logging
import hashlib
import hmac
import MySQLdb
from flask import Flask, request, redirect

logging.basicConfig(level=logging.ERROR)

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', '')
    db_name = os.getenv('DB_NAME', 'test')
    conn = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name, charset='utf8mb4')
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return "false"
        stored_hash = row[0]
        if isinstance(stored_hash, bytes):
            stored_hash = stored_hash.decode('utf-8')
        supplied_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if hmac.compare_digest(stored_hash, supplied_hash):
            return "true"
        return "false"
    except MySQLdb.Error as e:
        logging.error(e)
        return "false"
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run()