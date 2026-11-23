import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD', 'password')
    db = os.getenv('DB_NAME', 'cwe_900')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        exists = cursor.fetchone()
        if exists:
            return "Username already exists"
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return "You have successfully registered"
    except Exception:
        conn.rollback()
        return "Registration Failed"
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT 1 FROM users WHERE username=%s AND password=%s", (username, password))
        user = cursor.fetchone()
        if user:
            return "Login successful"
        else:
            return "Invalid credentials"
    finally:
        cursor.close()
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    new_email = request.form.get('email')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE users SET email=%s WHERE username=%s", (new_email, username))
        conn.commit()
        return "Profile updated successfully"
    finally:
        cursor.close()
        conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT username FROM users WHERE username LIKE CONCAT('%%', %s, '%%')", (term,))
        rows = cursor.fetchall()
        return ', '.join(row[0] for row in rows)
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username')
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
        return "Account deleted successfully"
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)