import os
import sys
import time
import logging
import re
import secrets
import threading
from datetime import timedelta
import MySQLdb
import MySQLdb.cursors
from flask import Flask, request, redirect, abort, url_for, escape, session
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(stream=sys.stderr, level=logging.ERROR)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=0, x_port=0, x_prefix=0)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PREFERRED_URL_SCHEME='https',
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    MAX_CONTENT_LENGTH=2 * 1024 * 1024
)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_urlsafe(32)

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_.-]{1,150}$')

_login_lock = threading.Lock()
_login_attempts = {}
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 15 * 60

def _clean_old_attempts():
    now = time.time()
    with _login_lock:
        for ip in list(_login_attempts.keys()):
            if now - _login_attempts[ip]['first'] > _WINDOW_SECONDS:
                del _login_attempts[ip]

def _is_rate_limited(ip):
    _clean_old_attempts()
    with _login_lock:
        entry = _login_attempts.get(ip)
        return entry is not None and entry['count'] >= _MAX_ATTEMPTS

def _record_failed_attempt(ip):
    now = time.time()
    with _login_lock:
        entry = _login_attempts.get(ip)
        if entry and now - entry['first'] <= _WINDOW_SECONDS:
            entry['count'] += 1
        else:
            _login_attempts[ip] = {'count': 1, 'first': now}

def get_db_connection():
    required = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise RuntimeError('Missing environment variables: ' + ', '.join(missing))
    conn_kwargs = {
        'host': os.getenv('DB_HOST'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD'),
        'db': os.getenv('DB_NAME'),
        'charset': 'utf8mb4',
        'use_unicode': True,
        'cursorclass': MySQLdb.cursors.DictCursor
    }
    ssl_ca = os.getenv('DB_SSL_CA')
    ssl_cert = os.getenv('DB_SSL_CERT')
    ssl_key = os.getenv('DB_SSL_KEY')
    if ssl_ca or ssl_cert or ssl_key:
        conn_kwargs['ssl'] = {}
        if ssl_ca:
            conn_kwargs['ssl']['ca'] = ssl_ca
        if ssl_cert:
            conn_kwargs['ssl']['cert'] = ssl_cert
        if ssl_key:
            conn_kwargs['ssl']['key'] = ssl_key
    return MySQLdb.connect(**conn_kwargs)

def _request_is_secure():
    return request.is_secure

@app.before_request
def enforce_https():
    if not app.debug and not _request_is_secure():
        return redirect(request.url.replace('http://', 'https://'), code=301)

@app.route('/login', methods=['POST'])
def login():
    ip = request.access_route[0] if request.access_route else request.remote_addr or 'unknown'
    if _is_rate_limited(ip):
        abort(429, description='Too many login attempts. Please try again later.')
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or not password:
        abort(400, description='Username and password are required.')
    if not USERNAME_REGEX.fullmatch(username):
        abort(400, description='Invalid username format.')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT username, password_hash FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
    except Exception as e:
        logger.error('Database error: %s', e)
        row = None
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception as e:
                logger.error('Cursor close error: %s', e)
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.error('Connection close error: %s', e)
    if row and check_password_hash(row['password_hash'], password):
        session.clear()
        session['username'] = username
        session.permanent = True
        return redirect(url_for('cwe200_user', username=username))
    _record_failed_attempt(ip)
    return redirect(url_for('cwe200'))

@app.route('/cwe200/<username>', methods=['GET'])
def cwe200_user(username):
    escaped_username = escape(username)
    return f'Welcome, {escaped_username}!'

@app.route('/cwe200/', methods=['GET'])
def cwe200():
    return 'Login failed.'

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', '5000'))
    app.run(host='0.0.0.0', port=port)