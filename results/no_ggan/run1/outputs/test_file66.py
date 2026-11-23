from flask import Flask, request, redirect, url_for
import re
import os
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return redirect(url_for('register'))
    if not re.fullmatch(r'[A-Za-z0-9_]{3,30}', username):
        return redirect(url_for('register'))
    pw_hash = generate_password_hash(password)
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    passwd = os.getenv('DB_PASSWORD', 'test123')
    dbname = os.getenv('DB_NAME', 'TESTDB')
    conn = None
    cur = None
    try:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=dbname, charset='utf8mb4')
        cur = conn.cursor()
        cur.execute('SELECT 1 FROM User WHERE Username = %s', (username,))
        if cur.fetchone():
            return redirect(url_for('register'))
        cur.execute('INSERT INTO User (Username, Password) VALUES (%s, %s)', (username, pw_hash))
        conn.commit()
    except MySQLdb.Error:
        return redirect(url_for('register'))
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return "Login page placeholder"

if __name__ == '__main__':
    app.run()