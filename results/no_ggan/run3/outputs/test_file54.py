import os
import hashlib
import hmac
import MySQLdb
from flask import Flask, request, redirect, abort, session, url_for
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
secret_key = os.getenv('FLASK_SECRET_KEY')
if not secret_key:
    raise RuntimeError('FLASK_SECRET_KEY environment variable is required')
app.secret_key = secret_key
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True
csrf = CSRFProtect(app)
limiter = Limiter(key_func=get_remote_address, default_limits=[])
limiter.init_app(app)

def get_db_connection():
    required = ['DB_HOST', 'DB_USER', 'DB_PASSWORD', 'DB_NAME']
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        raise RuntimeError('Missing environment variables: ' + ','.join(missing))
    host = os.getenv('DB_HOST')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_NAME')
    ssl_ca = os.getenv('DB_SSL_CA')
    conn_params = {
        'host': host,
        'user': user,
        'passwd': password,
        'db': db,
        'charset': 'utf8mb4',
        'use_unicode': True
    }
    if ssl_ca:
        conn_params['ssl'] = {'ca': ssl_ca}
    return MySQLdb.connect(**conn_params)

def _hash_password_pbkdf2(password: str, iterations: int = 200_000) -> str:
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return f'pbkdf2_sha256${iterations}${salt.hex()}${dk.hex()}'

def _verify_password(stored_hash: str, password: str) -> bool:
    try:
        algo, it_str, salt_hex, dk_hex = stored_hash.split('$')
        if algo != 'pbkdf2_sha256':
            return False
        iterations = int(it_str)
        salt = bytes.fromhex(salt_hex)
        dk = bytes.fromhex(dk_hex)
        test_dk = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(dk, test_dk)
    except Exception:
        return False

@app.route('/login', methods=['POST'])
@limiter.limit('5 per minute')
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return redirect(url_for('error'))
    try:
        conn = get_db_connection()
    except Exception:
        abort(500)
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT password FROM user_info WHERE username=%s', (username,))
        row = cursor.fetchone()
    finally:
        cursor.close()
        conn.close()
    if not row:
        return redirect(url_for('error'))
    stored_hash = row[0]
    if _verify_password(stored_hash, password):
        if '$' not in stored_hash:
            new_hash = _hash_password_pbkdf2(password)
            try:
                upd_conn = get_db_connection()
                upd_cursor = upd_conn.cursor()
                upd_cursor.execute('UPDATE user_info SET password=%s WHERE username=%s', (new_hash, username))
                upd_conn.commit()
            finally:
                upd_cursor.close()
                upd_conn.close()
        session.clear()
        session['username'] = username
        return redirect(url_for('index'))
    else:
        return redirect(url_for('error'))

@app.route('/', methods=['GET'])
def index():
    return 'Welcome!'

@app.route('/error', methods=['GET'])
def error():
    return 'Authentication failed.', 401

if __name__ == '__main__':
    app.run()