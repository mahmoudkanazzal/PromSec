import os
import time
import threading
import logging
from collections import defaultdict
from datetime import timedelta
import MySQLdb
from flask import Flask, request, redirect, url_for, session, abort, after_this_request, make_response
from werkzeug.security import check_password_hash
from werkzeug.middleware.proxy_fix import ProxyFix

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

_secret_key = os.getenv('FLASK_SECRET_KEY')
if not _secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable is missing')
app.secret_key = _secret_key

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
app.permanent_session_lifetime = timedelta(minutes=30)
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

_login_attempts = defaultdict(list)
_login_attempts_lock = threading.Lock()
_MAX_ATTEMPTS = 5
_WINDOW_SECONDS = 900

def get_db_connection():
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASS')
    db = os.getenv('DB_NAME')
    if not all([host, user, password, db]):
        raise RuntimeError('Database environment variables are missing')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True, autocommit=True)

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

def _get_client_ip():
    return request.remote_addr or 'unknown'

@app.route('/', methods=['GET'])
def index():
    return 'Welcome. POST username and password to /login.', 200, {'Content-Type': 'text/plain'}

@app.route('/login', methods=['POST'])
def login():
    client_ip = _get_client_ip()
    now = time.time()
    with _login_attempts_lock:
        attempts = _login_attempts[client_ip]
        attempts = [t for t in attempts if now - t < _WINDOW_SECONDS]
        _login_attempts[client_ip] = attempts
        if len(attempts) >= _MAX_ATTEMPTS:
            abort(429, description='Too many login attempts. Please try again later.')
    username = request.form.get('username', '').strip()
    password = request.form.get('password')
    if not username or not password:
        return redirect(url_for('index'))
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, pass FROM users WHERE username=%s', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row[1], password):
            with _login_attempts_lock:
                _login_attempts.pop(client_ip, None)
            session.clear()
            session['user_id'] = row[0]
            return redirect(url_for('dashboard'))
        else:
            with _login_attempts_lock:
                _login_attempts[client_ip].append(now)
            return redirect(url_for('index'))
    except MySQLdb.Error as e:
        logger.error('Database error: %s', e)
        with _login_attempts_lock:
            _login_attempts[client_ip].append(now)
        return redirect(url_for('index'))
    finally:
        if cur:
            try:
                cur.close()
            except Exception as e:
                logger.debug('Cursor close error: %s', e)
        if conn:
            try:
                conn.close()
            except Exception as e:
                logger.debug('Connection close error: %s', e)

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return f'Welcome, user {session["user_id"]}!'

if __name__ == '__main__':
    # In production, use a WSGI server and upstream HTTPS termination.
    app.run(host='0.0.0.0', port=5000, debug=False)