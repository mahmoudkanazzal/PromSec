# This file was assembled by gen.py, written by redactedAuthorFirstname redactedAuthorLastname.
import os
import hashlib
import re
from flask import Flask, request, redirect, abort
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default-secret-key')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'TESTDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400, description="Username and password are required.")
    password_hash = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM User WHERE Username = %s", (username,))
        if cursor.fetchone():
            return redirect('/register')
        cursor.execute("INSERT INTO User (Username, PasswordHash) VALUES (%s, %s)", (username, password_hash))
        conn.commit()
    except MySQLdb.Error:
        abort(500, description="Database error.")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    return redirect('/login')

if __name__ == '__main__':
    app.run()