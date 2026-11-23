"""Assembled by gen.py. Author: Placeholder Name."""
import os
import MySQLdb
from flask import Flask, request
from werkzeug.security import check_password_hash

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASSWORD', '')
    db = os.getenv('DB_NAME', 'db')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not isinstance(username, str) or not isinstance(password, str):
        return "username not found"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT username, password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
    if not row or row.get('username') != username:
        return "username not found"
    stored_hash = row.get('password')
    if stored_hash and check_password_hash(stored_hash, password):
        return "success"
    return "wrong pw"

if __name__ == '__main__':
    app.run()