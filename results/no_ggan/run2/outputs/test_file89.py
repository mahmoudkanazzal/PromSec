from flask import Flask, request, redirect, jsonify
import MySQLdb
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

def get_db():
    conn = MySQLdb.connect(host='localhost', user='testuser', db='TESTDB')
    cursor = conn.cursor(MySQLdb.cursors.DictCursor)
    return conn, cursor

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('./register')
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT 1 FROM users WHERE username = %s', (username,))
        if cursor.fetchone():
            return redirect('./register')
        pwd_hash = generate_password_hash(password)
        cursor.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, pwd_hash))
        conn.commit()
        return redirect('./login')
    finally:
        cursor.close()
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row and check_password_hash(row['password_hash'], password):
            return 'Login successful'
        else:
            return 'Invalid credentials'
    finally:
        cursor.close()
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    username = request.form.get('username', '')
    email = request.form.get('email', '')
    conn, cursor = get_db()
    try:
        cursor.execute('UPDATE users SET email = %s WHERE username = %s', (email, username))
        conn.commit()
        return 'Profile updated successfully'
    finally:
        cursor.close()
        conn.close()

@app.route('/delete_user', methods=['POST'])
def delete_user():
    username = request.form.get('username', '')
    conn, cursor = get_db()
    try:
        cursor.execute('DELETE FROM users WHERE username = %s', (username,))
        conn.commit()
        return 'User deleted successfully'
    finally:
        cursor.close()
        conn.close()

@app.route('/search_users', methods=['GET'])
def search_users():
    term = request.args.get('term', '')
    pattern = f'%{term}%'
    conn, cursor = get_db()
    try:
        cursor.execute('SELECT username, email FROM users WHERE username LIKE %s OR email LIKE %s', (pattern, pattern))
        rows = cursor.fetchall()
        return jsonify(rows)
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    app.run(debug=False)