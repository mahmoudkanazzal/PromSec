from __future__ import annotations
import os
from flask import Flask, request, redirect
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')
DB_NAME = os.getenv('DB_NAME', 'TESTDB')

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    email = request.form.get('email')
    if not username or not password:
        return redirect('./register')
    hashed_password = generate_password_hash(password)
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM users WHERE Username = %s", (username,))
            if cursor.fetchone():
                return redirect('./register')
            cursor.execute(
                "INSERT INTO users (Username, Password, Email) VALUES (%s, %s, %s)",
                (username, hashed_password, email)
            )
            conn.commit()
    return redirect('./login')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Invalid credentials"
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT Password FROM users WHERE Username = %s", (username,))
            row = cursor.fetchone()
            if row and check_password_hash(row['Password'], password):
                return "Login successful"
    return "Invalid credentials"

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    if not username or not email:
        return "Profile updated successfully"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(
                "UPDATE users SET Email = %s WHERE Username = %s",
                (email, username)
            )
            conn.commit()
    return "Profile updated successfully"

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    if not username:
        return "User deleted successfully"
    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM users WHERE Username = %s", (username,))
            conn.commit()
    return "User deleted successfully"

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cursor:
            cursor.execute(
                "SELECT Username, Email FROM users WHERE Username LIKE %s",
                (pattern,)
            )
            rows = cursor.fetchall()
    return str(rows)

if __name__ == '__main__':
    app.run(debug=False)