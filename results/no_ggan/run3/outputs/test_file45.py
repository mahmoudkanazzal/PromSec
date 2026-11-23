import os
import time
import logging
from flask import Flask, request, redirect, url_for, session, abort, make_response
import MySQLdb
import MySQLdb.cursors
from werkzeug.security import check_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_LOGIN_ATTEMPTS = 5
BLOCK_TIME_SECONDS = 15 * 60
_login_attempts = {}

def _is_ip_blocked(ip: str) -> bool:
    now = time.time()
    expired_ips = [addr for addr, data in _login_attempts.items()
                   if now - data['first'] >= BLOCK_TIME_SECONDS]
    for addr in expired_ips:
        _login_attempts.pop(addr, None)
    data = _login_attempts.get(ip)
    if not data:
        return False
    if data['count'] >= MAX_LOGIN_ATTEMPTS and now - data['first'] < BLOCK_TIME_SECONDS:
        return True
    return False

def _record_login_attempt(ip: str, success: bool) -> None:
    now = time.time()
    if success:
        _login_attempts.pop(ip, None)
        return
    entry = _login_attempts.get(ip)
    if entry:
        entry['count'] += 1
    else:
        _login_attempts[ip] = {'count': 1, 'first': now}

def get_client_ip() -> str:
    xff = request.headers.get('X-Forwarded-For')
    if xff:
        ip = xff.split(',')[0].strip()
        if ip:
            return ip
    if request.remote_addr:
        return request.remote_addr
    return 'unknown'

def get_db_connection():
    required = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise RuntimeError(f"Missing environment variables: {', '.join(missing)}")
    return MySQLdb.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASSWORD'),
        db=os.getenv('DB_NAME'),
        charset='utf8mb4',
        use_unicode=True,
        cursorclass=MySQLdb.cursors.DictCursor,
        autocommit=True
    )

def verify_password(stored_hash: str, password: str) -> bool:
    return check_password_hash(stored_hash, password)

app = Flask(__name__)

secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    raise RuntimeError("Missing environment variable: FLASK_SECRET_KEY")
app.secret_key = secret_key

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE='Strict',
    SESSION_PROTECTION='strong',
    PREFERRED_URL_SCHEME='https'
)

@app.after_request
def set_security_headers(response):
    headers = {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Content-Security-Policy': "default-src 'self'",
        'Referrer-Policy': 'no-referrer',
        'Cache-Control': 'no-store'
    }
    for k, v in headers.items():
        if k not in response.headers:
            response.headers[k] = v
    return response

@app.route('/login', methods=['POST'])
def login():
    ip = get_client_ip()
    if _is_ip_blocked(ip):
        abort(429)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        _record_login_attempt(ip, False)
        return redirect(url_for('login'))
    conn = None
    cur = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, role, password_hash FROM users WHERE username = %s", (username,))
        row = cur.fetchone()
        if not row or not verify_password(row['password_hash'], password):
            _record_login_attempt(ip, False)
            return redirect(url_for('login'))
        _record_login_attempt(ip, True)
        session.clear()
        session['user_id'] = row['id']
        session['role'] = row['role']
        return redirect(url_for('dashboard'))
    except MySQLdb.Error as e:
        logger.error(f"Database error: {e}")
        abort(500)
    finally:
        try:
            if cur:
                cur.close()
        except Exception as e:
            logger.debug(f"Error closing cursor: {e}")
        try:
            if conn:
                conn.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")

if __name__ == '__main__':
    # In production, use a WSGI server instead of the development server.
    app.run(debug=False)