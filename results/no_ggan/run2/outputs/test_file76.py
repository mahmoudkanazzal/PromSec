import os
import re
import logging
import secrets
import bcrypt
import MySQLdb
from contextlib import contextmanager
from flask import Flask, request, redirect, url_for, session as flask_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Strict'

def get_db_connection():
    host = os.getenv('DATABASE_URL', 'localhost')
    user = os.getenv('DATABASE_USER', 'root')
    password = os.getenv('DATABASE_PASSWORD', '')
    db = os.getenv('DATABASE_NAME', 'app')
    return MySQLdb.connect(host=host,
                           user=user,
                           passwd=password,
                           db=db,
                           charset='utf8mb4',
                           use_unicode=True,
                           autocommit=False)

@contextmanager
def db_cursor():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        yield conn, cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

USERNAME_REGEX = r'^[A-Za-z0-9_]{3,30}$'
EMAIL_REGEX = r'^[^@\s]+@[^@\s]+\.[^@\s]+$'

def is_valid_username(username: str) -> bool:
    return re.fullmatch(USERNAME_REGEX, username) is not None

def is_valid_email(email: str) -> bool:
    return re.fullmatch(EMAIL_REGEX, email) is not None

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.form.get('username', '').strip()
        name = request.form.get('name', '').strip()
        cweid = request.form.get('cweid', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            return 'Missing credentials', 400

        if not is_valid_username(username):
            return 'Invalid username format', 400

        if email and not is_valid_email(email):
            return 'Invalid email format', 400

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        with db_cursor() as (conn, cursor):
            cursor.execute('SELECT user_id FROM users WHERE username = %s', (username,))
            if cursor.fetchone():
                return 'Username is already taken', 409

            cursor.execute(
                'INSERT INTO users (username, password, name, email, cweid) VALUES (%s, %s, %s, %s, %s)',
                (username, hashed_pw, name or None, email or None, cweid or None)
            )
            user_id = cursor.lastrowid

            session_id = secrets.token_urlsafe(32)
            cursor.execute(
                'INSERT INTO sessions (username, user_id, session_id) VALUES (%s, %s, %s)',
                (username, user_id, session_id)
            )

        flask_session['session_id'] = session_id
        flask_session['user_id'] = user_id
        flask_session['username'] = username

        return redirect(url_for('login'))
    except Exception:
        logger.exception('Error during registration')
        return 'Internal server error', 500

if __name__ == '__main__':
    app.run()