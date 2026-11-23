from flask import Flask, request, redirect
import os
import subprocess
import sys
import hashlib
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return "Login failed!"
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return "Login failed!"
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return f"Welcome {username}!"
        return "Login failed!"
    except Exception:
        return "Login failed!"
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run()