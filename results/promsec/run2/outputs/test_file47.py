import os
import hashlib
import secrets
import MySQLdb
from flask import Flask, request

app = Flask(__name__)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    db_host = os.getenv('DB_HOST', 'localhost')
    db_user = os.getenv('DB_USER', 'root')
    db_pass = os.getenv('DB_PASS', 'root')
    db_name = os.getenv('DB_NAME', 'db')
    conn = None
    cursor = None
    try:
        conn = MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM user WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return "Login failed!"
        stored_hash = row[0]
        computed_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        if secrets.compare_digest(str(stored_hash), computed_hash):
            return f"Welcome {username}!"
        return "Login failed!"
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()

# In production, use a WSGI server instead of Flask's built-in server
if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000, debug=False)