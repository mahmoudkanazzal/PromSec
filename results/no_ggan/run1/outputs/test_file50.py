import os
import re
import logging
import MySQLdb
from flask import Flask, request, abort, jsonify, make_response
from passlib.hash import pbkdf2_sha256

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

secret = os.getenv('FLASK_SECRET_KEY')
if secret:
    app.secret_key = secret
else:
    generated = os.urandom(32)
    app.secret_key = generated
    logger.warning('FLASK_SECRET_KEY not set, using generated key')

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = False

_USERNAME_RE = re.compile(r'^\w{1,64}$')

def _get_db_connection():
    host = os.getenv('MYSQL_HOST', 'localhost')
    user = os.getenv('MYSQL_USER', 'root')
    password = os.getenv('MYSQL_PASSWORD', '')
    db = os.getenv('MYSQL_DB', 'test')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True)

def _verify_password(plain_password, stored_hash):
    if not stored_hash.startswith("$pbkdf2-sha256$"):
        return False
    return pbkdf2_sha256.verify(plain_password, stored_hash)

def _needs_rehash(stored_hash):
    return pbkdf2_sha256.needs_update(stored_hash)

@app.after_request
def _set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password or not _USERNAME_RE.match(username):
        return jsonify(message="Invalid credentials"), 400
    conn = None
    cursor = None
    try:
        conn = _get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE username=%s", (username,))
        row = cursor.fetchone()
        if not row:
            return jsonify(message="Invalid credentials"), 401
        stored_hash = row[0]
        if _verify_password(password, stored_hash):
            if _needs_rehash(stored_hash):
                new_hash = pbkdf2_sha256.hash(password)
                try:
                    cursor.execute("UPDATE users SET password=%s WHERE username=%s", (new_hash, username))
                    conn.commit()
                except MySQLdb.Error as e:
                    logger.error("Error updating password hash: %s", e)
            return jsonify(message="Login Success"), 200
        else:
            return jsonify(message="Invalid credentials"), 401
    except MySQLdb.Error as e:
        logger.exception("Database error")
        return jsonify(message="Server error"), 500
    finally:
        if cursor:
            try:
                cursor.close()
            except Exception:
                logger.debug("Error closing cursor")
        if conn:
            try:
                conn.close()
            except Exception:
                logger.debug("Error closing connection")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)