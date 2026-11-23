from flask import Flask, request, redirect, url_for
import os
import MySQLdb
from werkzeug.security import generate_password_hash

app = Flask(__name__)

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'testuser')
    password = os.getenv('DB_PASSWORD', 'test123')
    db = os.getenv('DB_NAME', 'TESTDB')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db)

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return redirect(url_for('register'))
    hashed = generate_password_hash(password)
    conn = get_db_connection()
    cursor = None
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM User WHERE Username = %s', (username,))
        if cursor.fetchone():
            return redirect(url_for('register'))
        cursor.execute('INSERT INTO User (Username, Password) VALUES (%s, %s)', (username, hashed))
        conn.commit()
    finally:
        if cursor:
            cursor.close()
        conn.close()
    return redirect(url_for('login'))