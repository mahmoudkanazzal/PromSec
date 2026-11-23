import os
import sys
import time
import threading
import secrets
import logging
import MySQLdb
import bcrypt
from datetime import timedelta
from flask import Flask, request, redirect, session, abort, make_response

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

flask_secret = os.getenv('FLASK_SECRET_KEY')
if flask_secret is None:
    logger.warning('FLASK_SECRET_KEY not set, generating random secret')
    flask_secret = secrets.token_bytes(32)
else:
    flask_secret = flask_secret.encode() if isinstance(flask_secret, str) else flask_secret
app.secret_key = flask_secret

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD')
if not DB_PASSWORD:
    raise RuntimeError('Environment variable DB_PASSWORD is required')
DB_NAME = os.getenv('DB_NAME', 'cwe200')
DB_SSL_CA = os.getenv('DB_SSL_CA')

def get_db_connection():
    conn_params = {
        'host': DB_HOST,
        'user': DB_USER,
        'passwd': DB_PASSWORD,
        'db': DB_NAME,
        'charset': 'utf8mb4',
        'use_unicode': True,
    }
    if DB_SSL_CA:
        conn_params['ssl'] = {'ca': DB_SSL_CA}
    return MySQLdb.connect(**conn_params)

MAX_USERNAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 128

login_attempts = {}
login_attempts_lock = threading.Lock()
RATE_LIMIT = 5
WINDOW_SECONDS = 60

def get_client_ip():
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        return xff.split(',')[0].strip()
    return request.remote_addr or '0.0.0.0'

def is_rate_limited(ip):
    now = time.time()
    with login_attempts_lock:
        attempts = login_attempts.get(ip, [])
        attempts = [t for t in attempts if now - t < WINDOW_SECONDS]
        attempts.append(now)
        login_attempts[ip] = attempts
        if len(attempts) > RATE_LIMIT:
            return True
        if not attempts:
            login_attempts.pop(ip, None)
        return False

@app.route('/login', methods=['POST'])
def login():
    ip = get_client_ip()
    if is_rate_limited(ip):
        return make_response('Too many login attempts, try later.', 429)

    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or password is None:
        return make_response('Missing username or password.', 400)

    if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return make_response('Input too long.', 400)

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if row:
            stored_hash = row[0]
            if isinstance(stored_hash, str):
                stored_hash = stored_hash.encode('utf-8')
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                session.clear()
                session['username'] = username
                session.permanent = True
                return redirect('/session')
        return make_response('Invalid credentials.', 401)
    except MySQLdb.Error:
        logger.exception('Database error during login')
        return make_response('Service unavailable.', 503)
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                logger.debug('Failed to close cursor')
        if conn:
            try:
                conn.close()
            except Exception:
                logger.debug('Failed to close connection')

if __name__ == '__main__':
    # In production, use a WSGI server and terminate TLS upstream
    app.run(host='0.0.0.0', port=5000)