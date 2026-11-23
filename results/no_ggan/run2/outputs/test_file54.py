import os
import MySQLdb
from flask import Flask, request, redirect, session, abort
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER')
    password = os.getenv('DB_PASSWORD')
    db = os.getenv('DB_NAME')
    missing = []
    if not user:
        missing.append('DB_USER')
    if not password:
        missing.append('DB_PASSWORD')
    if not db:
        missing.append('DB_NAME')
    if missing:
        raise RuntimeError('Missing environment variables: ' + ', '.join(missing))
    return MySQLdb.connect(host=host, user=user, passwd=password, db=db, charset='utf8mb4', use_unicode=True, autocommit=True)

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        abort(400)
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT password FROM user_info WHERE username = %s', (username,))
        row = cursor.fetchone()
        if not row:
            return redirect('/error')
        if check_password_hash(row['password'], password):
            session.clear()
            session['username'] = username
            return redirect('/')
        return redirect('/error')
    finally:
        if conn:
            conn.close()