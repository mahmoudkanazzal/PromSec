import os
from flask import Flask, request, redirect, url_for
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'default_secret')

DB_CONFIG = {
    "host": os.getenv('DB_HOST', 'localhost'),
    "user": os.getenv('DB_USER', 'root'),
    "passwd": os.getenv('DB_PASSWORD', ''),
    "db": os.getenv('DB_NAME', 'testdb'),
    "charset": os.getenv('DB_CHARSET', 'utf8mb4')
}

def get_db_connection():
    return MySQLdb.connect(**DB_CONFIG)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect(url_for('register_page'))
    hashed = generate_password_hash(password)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM User WHERE Username = %s", (username,))
        if cursor.fetchone():
            return redirect(url_for('register_page'))
        cursor.execute("INSERT INTO User (Username, Password) VALUES (%s, %s)", (username, hashed))
        conn.commit()
        return redirect(url_for('login_page'))
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return "Invalid credentials"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Password FROM User WHERE Username = %s", (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row[0], password):
            return "Login successful"
        else:
            return "Invalid credentials"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    if not username or not email:
        return "Profile updated successfully"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE User SET Email = %s WHERE Username = %s", (email, username))
        conn.commit()
        return "Profile updated successfully"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    if not username:
        return "User deleted successfully"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM User WHERE Username = %s", (username,))
        conn.commit()
        return "User deleted successfully"
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM User WHERE Username LIKE %s", (pattern,))
        users = cursor.fetchall()
        return str(users)
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)