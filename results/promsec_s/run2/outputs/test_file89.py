import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'testuser')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'test123')
DB_NAME = os.getenv('DB_NAME', 'TESTDB')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return redirect("./register")
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return redirect("./login")
        finally:
            cursor.close()
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT 1 FROM users WHERE username = %s AND password = %s", (username, password))
            if cursor.fetchone():
                return "Login successful"
            else:
                return "Invalid credentials"
        finally:
            cursor.close()
    finally:
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE users SET email = %s WHERE username = %s", (email, username))
            conn.commit()
            return "Profile updated successfully"
        finally:
            cursor.close()
    finally:
        conn.close()

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM users WHERE username = %s", (username,))
            conn.commit()
            return "User deleted successfully"
        finally:
            cursor.close()
    finally:
        conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        try:
            like_term = f"%{term}%"
            cursor.execute("SELECT username, email FROM users WHERE username LIKE %s", (like_term,))
            rows = cursor.fetchall()
            return str(rows)
        finally:
            cursor.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)