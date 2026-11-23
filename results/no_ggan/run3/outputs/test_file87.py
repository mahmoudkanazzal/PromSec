import os
import bcrypt
import MySQLdb
from flask import Flask, request

def get_db_connection():
    host = os.getenv('DB_HOST', '127.0.0.1')
    user = os.getenv('DB_USER', 'app_user')
    password = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'cwe_900')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return "Registration Failed"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            return "Username already exists"
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed.decode('utf-8')))
        conn.commit()
        return "You have successfully registered"
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return "Registration Failed"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return "Invalid credentials"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password FROM users WHERE username=%s", (username,))
        row = cur.fetchone()
        if row:
            stored_hash = row[0].encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                return "Login successful"
        return "Invalid credentials"
    except MySQLdb.Error:
        return "Invalid credentials"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username', '')
    email = request.form.get('email', '')
    if not username or not email:
        return "Update Failed"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET email=%s WHERE username=%s", (email, username))
        conn.commit()
        return "Profile updated successfully"
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return "Update Failed"
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
        cur.execute("SELECT username FROM users WHERE username LIKE %s", (pattern,))
        rows = cur.fetchall()
        usernames = [row[0] for row in rows]
        return str(usernames)
    except MySQLdb.Error:
        return "Search Failed"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username', '')
    if not username:
        return "Deletion Failed"
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM users WHERE username=%s", (username,))
        conn.commit()
        return "Account deleted successfully"
    except MySQLdb.Error:
        if conn:
            conn.rollback()
        return "Deletion Failed"
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)