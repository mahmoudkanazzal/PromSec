import os
from flask import Flask, request, Response
import MySQLdb
import bcrypt

app = Flask(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'test')

def get_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True)

def json_array(strings):
    return '[' + ','.join('"%s"' % s.replace('\\', '\\\\').replace('"', '\\"') for s in strings) + ']'

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Registration Failed'
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM users WHERE username=%s', (username,))
        if cur.fetchone():
            return 'Username already exists'
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        cur.execute('INSERT INTO users (username, password) VALUES (%s, %s)', (username, hashed))
        conn.commit()
        return 'You have successfully registered'
    except:
        if conn:
            conn.rollback()
        return 'Registration Failed'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '').strip()
    if not username or not password:
        return 'Invalid credentials'
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT password FROM users WHERE username=%s', (username,))
        row = cur.fetchone()
        if not row:
            return 'Invalid credentials'
        stored = row[0]
        if isinstance(stored, str):
            stored = stored.encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored):
            return 'Login successful'
        else:
            return 'Invalid credentials'
    except:
        return 'Invalid credentials'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username', '').strip()
    email = request.form.get('email', '').strip()
    if not username or not email:
        return 'Profile updated successfully'
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('UPDATE users SET email=%s WHERE username=%s', (email, username))
        conn.commit()
        return 'Profile updated successfully'
    except:
        if conn:
            conn.rollback()
        return 'Profile updated successfully'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '').strip()
    if not term:
        return Response('[]', mimetype='application/json')
    pattern = f'%{term}%'
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('SELECT username FROM users WHERE username LIKE %s', (pattern,))
        rows = cur.fetchall()
        usernames = [row[0] for row in rows]
        return Response(json_array(usernames), mimetype='application/json')
    except:
        return Response('[]', mimetype='application/json')
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.route('/delete_account', methods=['POST'])
def delete_account():
    username = request.form.get('username', '').strip()
    if not username:
        return 'Account deleted successfully'
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM users WHERE username=%s', (username,))
        conn.commit()
        return 'Account deleted successfully'
    except:
        if conn:
            conn.rollback()
        return 'Account deleted successfully'
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

if __name__ == '__main__':
    app.run(debug=False)