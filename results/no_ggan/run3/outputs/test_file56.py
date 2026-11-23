import os
import time
import threading
import bcrypt
import MySQLdb
from flask import Flask, request, session, redirect, abort, escape, make_response

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASS = os.getenv('DB_PASS')
DB_NAME = os.getenv('DB_NAME', 'cwe200')
if DB_PASS is None:
    raise RuntimeError('DB_PASS environment variable must be set')

def get_db_connection():
    return MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASS, db=DB_NAME, charset='utf8mb4', use_unicode=True, autocommit=False)

LOGIN_ATTEMPTS = {}
ATTEMPT_LOCK = threading.Lock()
WINDOW = 60
MAX_ATTEMPTS = 5

def _prune(ip):
    now = time.time()
    attempts = LOGIN_ATTEMPTS.get(ip, [])
    attempts = [t for t in attempts if now - t < WINDOW]
    if attempts:
        LOGIN_ATTEMPTS[ip] = attempts
    else:
        LOGIN_ATTEMPTS.pop(ip, None)

def is_rate_limited(ip):
    with ATTEMPT_LOCK:
        _prune(ip)
        return len(LOGIN_ATTEMPTS.get(ip, [])) >= MAX_ATTEMPTS

def record_failed_attempt(ip):
    with ATTEMPT_LOCK:
        attempts = LOGIN_ATTEMPTS.get(ip, [])
        attempts.append(time.time())
        LOGIN_ATTEMPTS[ip] = attempts
        _prune(ip)

def clear_attempts(ip):
    with ATTEMPT_LOCK:
        LOGIN_ATTEMPTS.pop(ip, None)

@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response

def get_client_ip():
    forwarded = request.headers.get('X-Forwarded-For')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.remote_addr

@app.route('/login', methods=['POST'])
def login():
    ip = get_client_ip()
    if is_rate_limited(ip):
        abort(429)
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
        row = cursor.fetchone()
        if not row:
            record_failed_attempt(ip)
            abort(401)
        password_hash = row[0]
        if isinstance(password_hash, str):
            password_hash = password_hash.encode('utf-8')
        if not bcrypt.checkpw(password.encode('utf-8'), password_hash):
            record_failed_attempt(ip)
            abort(401)
        session.clear()
        session['username'] = username
        clear_attempts(ip)
        return redirect('/session')
    except MySQLdb.Error:
        abort(503)
    finally:
        if conn:
            conn.close()

@app.route('/session', methods=['GET'])
def session_view():
    if 'username' not in session:
        return redirect('/login')
    return make_response(f"<p>Logged in as {escape(session['username'])}</p>")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)