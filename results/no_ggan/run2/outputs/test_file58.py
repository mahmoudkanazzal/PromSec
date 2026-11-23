import os
import re
import logging
import MySQLdb
from flask import Flask, request, redirect, url_for, abort, escape, session, render_template_string
from werkzeug.security import check_password_hash
from flask_wtf.csrf import CSRFProtect

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))

CSRFProtect(app)

USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_]{1,150}$')

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    passwd = os.getenv('DB_PASS')
    if not passwd:
        raise RuntimeError('Database password not set in DB_PASS')
    db = os.getenv('DB_NAME', 'cwe200')
    ca = os.getenv('DB_SSL_CA')
    cert = os.getenv('DB_SSL_CERT')
    key = os.getenv('DB_SSL_KEY')
    if ca and cert and key:
        ssl_params = {'ca': ca, 'cert': cert, 'key': key}
    else:
        ssl_params = None
    return MySQLdb.connect(host=host, user=user, passwd=passwd, db=db,
                           charset='utf8mb4', use_unicode=True,
                           autocommit=True, ssl=ssl_params)

@app.route('/login', methods=['GET'])
def login_page():
    form_html = '''
    <form method="post" action="{{ url_for('login') }}">
        {{ csrf_token() }}
        <label for="username">Username:</label>
        <input type="text" name="username" id="username" required>
        <label for="password">Password:</label>
        <input type="password" name="password" id="password" required>
        <button type="submit">Login</button>
    </form>
    '''
    return render_template_string(form_html)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    if not username or not password or not USERNAME_REGEX.match(username):
        return redirect(url_for('login_page'))
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT username, password_hash FROM users WHERE username = %s', (username,))
        row = cursor.fetchone()
        if not row or not check_password_hash(row['password_hash'], password):
            return redirect(url_for('login_page'))
        session.clear()
        session['username'] = username
        return redirect(url_for('user_home', username=username))
    except MySQLdb.Error as e:
        app.logger.error('Database error: %s', e)
        abort(500)
    finally:
        try:
            if cursor:
                cursor.close()
        finally:
            if conn:
                conn.close()

@app.route('/cwe200/<username>', methods=['GET'])
def user_home(username):
    session_user = session.get('username')
    if session_user != username:
        return redirect(url_for('login_page'))
    escaped_username = escape(username)
    return f'Welcome, {escaped_username}!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)