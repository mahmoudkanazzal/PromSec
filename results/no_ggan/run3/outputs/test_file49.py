# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
from flask import Flask, request, redirect
import os
import hashlib
import MySQLdb

app = Flask(__name__)

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    pwd_hash = _hash_password(password)
    conn = _get_db_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM users WHERE username=%s AND pass=%s"
    cursor.execute(query, (username, pwd_hash))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    if result:
        return redirect('/dashboard')
    else:
        return redirect('/')

if __name__ == '__main__':
    app.run()