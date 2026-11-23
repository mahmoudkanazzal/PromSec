#!/usr/bin/env python3
import os
import sys
import time
import re
import pymysql
import bcrypt
from datetime import timedelta
from flask import Flask, request, redirect, session, abort, url_for

required_env = ['FLASK_SECRET_KEY', 'DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
missing = [var for var in required_env if not os.getenv(var)]
if missing:
    sys.stderr.write('Missing environment variables: ' + ', '.join(missing) + '\n')
    sys.exit(1)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Strict',
    PREFERRED_URL_SCHEME='https',
    SESSION_PROTECTION='strong',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024
)

_login_attempts = {}
_RATE_LIMIT_MAX = 5
_RATE_LIMIT_WINDOW = 15 * 60

def _prune_attempts(attempts, now):
    cutoff = now - _RATE_LIMIT_WINDOW
    return [t for t in attempts if t > cutoff]

def _is_rate_limited(key):
    now = int(time.time())
    attempts = _login_attempts.get(key, [])
    attempts = _prune_attempts(attempts, now)
    _login_attempts[key] = attempts
    return len(attempts) >= _RATE_LIMIT_MAX

def _record_login_attempt(key):
    now = int(time.time())
    attempts = _login_attempts.get(key, [])
    attempts.append(now)
    _login_attempts[key] = _prune_attempts(attempts, now)

def _clear_login_attempts(key):
    _login_attempts.pop(key, None)

def get_db_connection():
    kwargs = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'database': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.Cursor,
        'autocommit': True
    }
    if os.getenv('DB_SSL', '').lower() == 'true':
        kwargs['ssl'] = {'ssl': {}}
    return pymysql.connect(**kwargs)

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_]{1,150}$')

@app.route('/login', methods=['POST'], endpoint='login')
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        abort(400)
    if not USERNAME_REGEX.fullmatch(username):
        abort(400)
    if len(password) > 256:
        abort(400)
    client_ip = request.remote_addr or 'unknown'
    key = f'{username}:{client_ip}'
    if _is_rate_limited(key):
        abort(429)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT password_hash FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        if not row:
            _record_login_attempt(key)
            abort(401)
        stored_hash = row[0]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            _record_login_attempt(key)
            abort(401)
        session.clear()
        session['username'] = username
        _clear_login_attempts(key)
        return redirect(url_for('session_view'))
    except pymysql.MySQLError:
        abort(500)
    finally:
        if conn:
            conn.close()

@app.route('/session', endpoint='session_view')
def session_view():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return f"Welcome, {session['username']}!"

@app.route('/login', methods=['GET'], endpoint='login_page')
def login_page():
    return '''
<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Login</title></head>
<body>
<form action="/login" method="post">
<label>Username: <input type="text" name="username" required></label><br>
<label>Password: <input type="password" name="password" required></label><br>
<button type="submit">Login</button>
</form>
</body>
</html>
'''

if __name__ == '__main__':
    # In production, use a WSGI server such as gunicorn
    app.run(host='0.0.0.0', port=5000)