# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request
import os
import MySQLdb
from werkzeug.security import check_password_hash

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'root')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return "Bad Login", 400
    conn = None
    cursor = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    if not row:
        return "Bad Login", 401
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return "Good Login"
    return "Bad Login", 401