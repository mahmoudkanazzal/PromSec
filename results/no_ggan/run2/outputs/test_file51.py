# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import MySQLdb
import bcrypt

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'appuser')
    password = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Missing username or password", 400
    conn = _get_db_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        query = "SELECT id, username, password, accesslevel FROM user WHERE username = %s"
        cursor.execute(query, (username,))
        result = cursor.fetchone()
        if not result:
            return "User does not exist", 404
        stored_hash = result[2]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return "Incorrect Password", 401
        return redirect('/user')
    finally:
        if cursor is not None:
            cursor.close()
        conn.close()