import os
from flask import Flask, request, redirect
import MySQLdb

app = Flask(__name__)

def _get_connection():
    return MySQLdb.connect(host='localhost', user='root', passwd=os.getenv('DB_PASSWORD', ''), db='mysite', charset='utf8mb4')

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Registration failed'
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = %s", (username,))
        if cursor.fetchone():
            return 'Username already exists'
        cursor.execute("INSERT INTO user (username, password) VALUES (%s, %s)", (username, password))
        conn.commit()
        return redirect('/home')
    except MySQLdb.Error:
        return 'Registration failed'
    except Exception:
        return 'Registration failed'
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

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return 'Login failed'
    conn = None
    cursor = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM user WHERE username = %s AND password = %s", (username, password))
        if cursor.fetchone():
            return redirect('/dashboard')
        return 'Invalid credentials'
    except MySQLdb.Error:
        return 'Login failed'
    except Exception:
        return 'Login failed'
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
    app.run(debug=False)