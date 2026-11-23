from __future__ import annotations
import os
from flask import Flask, request, redirect, session
from MySQLdb import connect, OperationalError, ProgrammingError
from passlib.hash import bcrypt
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.getenv('SESSION_COOKIE_SECURE', '').lower() == 'true'

def get_db_connection():
    return connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DB')
    )

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect('/')
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        cursor.close()
    except (OperationalError, ProgrammingError):
        return redirect('/')
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    if not row:
        return redirect('/')
    stored_hash = row[0]
    if not bcrypt.verify(password, stored_hash):
        return redirect('/')
    session['user'] = username
    return redirect('/dashboard')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.getenv('PORT', '5000')))