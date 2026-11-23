import os
from flask import Flask, request, redirect
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'user')
DB_PASS = os.getenv('DB_PASS', 'password')
DB_NAME = os.getenv('DB_NAME', 'database')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='utf8mb4', use_unicode=True)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('./register')
    pw_hash = generate_password_hash(password)
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM Users WHERE Username = %s", (username,))
        if cur.fetchone():
            return redirect('./register')
        cur.execute("INSERT INTO Users (Username, Password) VALUES (%s, %s)", (username, pw_hash))
        conn.commit()
        return redirect('./login')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Invalid credentials"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Password FROM Users WHERE Username = %s", (username,))
        row = cur.fetchone()
        if row and check_password_hash(row[0], password):
            return "Login successful"
        else:
            return "Invalid credentials"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    if not username or not email:
        return "Missing data"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Users SET Email = %s WHERE Username = %s", (email, username))
        conn.commit()
        return "Profile updated successfully"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    if not username:
        return "Missing username"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM Users WHERE Username = %s", (username,))
        conn.commit()
        return "User deleted successfully"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT Username FROM Users WHERE Username LIKE %s", (pattern,))
        rows = cur.fetchall()
        return str(rows)
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)