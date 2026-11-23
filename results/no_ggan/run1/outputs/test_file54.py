import os
import secrets
import MySQLdb
from flask import Flask, request, redirect, session, abort, render_template_string
from werkzeug.security import check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or secrets.token_urlsafe(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
limiter = Limiter(app, key_func=get_remote_address, default_limits=[])

def _get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'root')
    password = os.getenv('DB_PASSWORD')
    name = os.getenv('DB_NAME', 'test')
    if password is None:
        raise RuntimeError('DB_PASSWORD environment variable is required')
    return MySQLdb.connect(host=host, user=user, password=password, db=name, charset='utf8mb4', use_unicode=True)

def _generate_csrf_token():
    token = secrets.token_urlsafe(32)
    session['csrf_token'] = token
    return token

def _validate_csrf_token(token):
    stored = session.get('csrf_token')
    return stored is not None and secrets.compare_digest(stored, token)

@app.route('/login', methods=['GET'])
def login_get():
    token = _generate_csrf_token()
    html = """
    <form method="post" action="/login">
        <input type="hidden" name="csrf_token" value="{{ token }}">
        <label>Username: <input type="text" name="username"></label><br>
        <label>Password: <input type="password" name="password"></label><br>
        <button type="submit">Login</button>
    </form>
    """
    return render_template_string(html, token=token)

@app.route('/login', methods=['POST'])
@limiter.limit("5 per minute")
def login_post():
    token = request.form.get('csrf_token', '')
    if not _validate_csrf_token(token):
        abort(400)
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password:
        return redirect('/error')
    conn = None
    try:
        conn = _get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT password_hash FROM user_info WHERE username = %s", (username,))
        row = cur.fetchone()
    except MySQLdb.Error:
        return redirect('/error')
    finally:
        if conn:
            conn.close()
    if not row:
        return redirect('/error')
    stored_hash = row[0]
    if check_password_hash(stored_hash, password):
        return redirect('/')
    return redirect('/error')

if __name__ == '__main__':
    app.run()