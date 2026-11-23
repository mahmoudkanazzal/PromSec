from flask import Flask, request, redirect
from werkzeug.security import generate_password_hash
import mysql.connector
from mysql.connector import Error
import os
import re

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return 'Username and password required', 400
    if not re.fullmatch(r'^[A-Za-z0-9_-]{3,30}$', username):
        return 'Invalid username', 400
    pwd_hash = generate_password_hash(password)
    conn = None
    cur = None
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO User (Username, Password, Email) VALUES (%s, %s, %s)",
            (username, pwd_hash, username)
        )
        conn.commit()
    except Error:
        return 'Database error', 500
    finally:
        try:
            if cur:
                cur.close()
        except Exception:
            pass
        try:
            if conn:
                conn.close()
        except Exception:
            pass
    return redirect('/')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)