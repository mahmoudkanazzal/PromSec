from flask import Flask, request, redirect
import os
import hashlib
import mysql.connector

app = Flask(__name__)

def verify_password(stored_hash, password):
    salt = os.getenv('PWD_SALT', '').encode()
    dk = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, 100000)
    return stored_hash == dk.hex()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Bad Login"
    conn = None
    cursor = None
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if row and verify_password(row['password'], password):
            return "Good Login"
        else:
            return "Bad Login"
    except Exception:
        return "Bad Login"
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                pass
        if conn:
            try:
                conn.close()
            except Exception:
                pass

if __name__ == '__main__':
    app.run()