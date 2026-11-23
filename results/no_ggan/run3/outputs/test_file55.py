import os
import hashlib
import hmac
import logging
import secrets
import contextlib
from flask import Flask, request, redirect, url_for
import MySQLdb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '')
DB_NAME = os.getenv('DB_NAME', 'testdb')
PBKDF2_ITERATIONS = int(os.getenv('PBKDF2_ITERATIONS', '200000'))
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))

SALT_SIZE = 16
HASH_NAME = 'sha256'
MAX_USERNAME_LENGTH = 150
MAX_PASSWORD_LENGTH = 256

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PREFERRED_URL_SCHEME'] = 'https'

def hash_password(password: str, salt: bytes = None) -> str:
    if salt is None:
        salt = secrets.token_bytes(SALT_SIZE)
    dk = hashlib.pbkdf2_hmac(HASH_NAME, password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"

def verify_password(stored: str, password: str) -> bool:
    try:
        if '$' in stored:
            salt_hex, hash_hex = stored.split('$', 1)
            salt = bytes.fromhex(salt_hex)
            dk = hashlib.pbkdf2_hmac(HASH_NAME, password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
            return hmac.compare_digest(dk.hex(), hash_hex)
        else:
            sha1_hash = hashlib.sha1(password.encode('utf-8')).hexdigest()
            return hmac.compare_digest(sha1_hash, stored)
    except Exception:
        return False

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return redirect(url_for('cant_login'))
    if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return redirect(url_for('cant_login'))
    conn = None
    try:
        conn = MySQLdb.connect(host=DB_HOST, user=DB_USER, passwd=DB_PASSWORD, db=DB_NAME, charset='utf8mb4', use_unicode=True, autocommit=False)
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username = %s", (username,))
        row = cursor.fetchone()
        if not row:
            return redirect(url_for('cant_login'))
        stored_hash = row[0]
        if verify_password(stored_hash, password):
            if '$' not in stored_hash:
                new_hash = hash_password(password)
                try:
                    cursor.execute("UPDATE users SET password = %s WHERE username = %s", (new_hash, username))
                    conn.commit()
                except Exception:
                    logger.exception("Password upgrade failed")
                    conn.rollback()
            return redirect(url_for('success'))
        else:
            return redirect(url_for('cant_login'))
    except Exception:
        logger.exception("Login processing error")
        return redirect(url_for('internal_server_error'))
    finally:
        if conn:
            with contextlib.suppress(Exception):
                conn.close()

@app.route('/success')
def success():
    return "Login successful", 200

@app.route('/cant_login')
def cant_login():
    return "Invalid credentials", 401

@app.route('/internal_server_error')
def internal_server_error():
    return "Internal server error", 500

if __name__ == '__main__':
    app.run(debug=False)