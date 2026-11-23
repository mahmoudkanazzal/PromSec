import os
import secrets
import logging
from contextlib import closing
from flask import Flask, request, redirect, session, abort
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
from flask_talisman import Talisman

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_urlsafe(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
secure_flag = os.getenv('FLASK_COOKIE_SECURE', '').lower() in ('true', '1', 'yes')
app.config['SESSION_COOKIE_SECURE'] = secure_flag
app.config['PERMANENT_SESSION_LIFETIME'] = 86400
CSRFProtect(app)
csp = {
    'default-src': ["'self'"],
    'script-src': ["'self'"],
    'style-src': ["'self'"],
    'img-src': ["'self'"],
    'font-src': ["'self'"]
}
Talisman(app, content_security_policy=csp, force_https=True, strict_transport_security=True, frame_deny=True, referrer_policy='no-referrer')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'appuser')
    password = os.getenv('DB_PASSWORD')
    if password is None:
        raise RuntimeError('DB_PASSWORD environment variable not set')
    db = os.getenv('DB_NAME', 'mysite')
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True, autocommit=False)

def _validate_username(username: str) -> bool:
    return bool(username) and len(username) <= 150 and username.isidentifier()

def _validate_password(password: str) -> bool:
    return bool(password) and 8 <= len(password) <= 128

@app.route('/register', methods=['POST'])
def register():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not _validate_username(username) or not _validate_password(password):
        abort(400)
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("SELECT 1 FROM users WHERE username=%s", (username,))
                if cursor.fetchone():
                    abort(409)
                pwd_hash = generate_password_hash(password)
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)", (username, pwd_hash))
                conn.commit()
        return redirect('/home')
    except MySQLdb.Error:
        logging.exception("Database error during registration")
        abort(500)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not _validate_username(username) or not _validate_password(password):
        abort(400)
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cursor:
                cursor.execute("SELECT password_hash FROM users WHERE username=%s", (username,))
                row = cursor.fetchone()
                if not row or not check_password_hash(row[0], password):
                    abort(401)
        session.clear()
        session['username'] = username
        return redirect('/dashboard')
    except MySQLdb.Error:
        logging.exception("Database error during login")
        abort(500)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=False)