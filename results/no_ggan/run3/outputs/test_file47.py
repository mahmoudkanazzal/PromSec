# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import os
import hashlib
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app')
    password = os.getenv('DB_PASS', '')
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
        cursor.execute("SELECT password_hash FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return "Login failed!"
        stored_hash = row[0]
        if check_password_hash(stored_hash, password):
            return f"Welcome {username}!"
        return "Login failed!"
    finally:
        if conn:
            conn.close()