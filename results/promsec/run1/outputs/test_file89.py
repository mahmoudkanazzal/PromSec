import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def get_connection():
    return MySQLdb.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', ''),
        passwd=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', '')
    )

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM users WHERE Username=%s", (username,))
            exists = cur.fetchone()
            if exists:
                return redirect('./register')
            cur.execute("INSERT INTO users (Username, Password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return redirect('./login')
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT 1 FROM users WHERE Username=%s AND Password=%s", (username, password))
            if cur.fetchone():
                return "Login successful"
            else:
                return "Invalid credentials"
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username')
    email = request.form.get('email')
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("UPDATE users SET Email=%s WHERE Username=%s", (email, username))
            conn.commit()
            return "Profile updated successfully"
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username')
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM users WHERE Username=%s", (username,))
            conn.commit()
            return "User deleted successfully"
        finally:
            cur.close()
    finally:
        conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f"%{term}%"
    conn = get_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute("SELECT Username, Email FROM users WHERE Username LIKE %s", (pattern,))
            rows = cur.fetchall()
            return str(rows)
        finally:
            cur.close()
    finally:
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)