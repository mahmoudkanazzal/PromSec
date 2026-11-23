import os
from flask import Flask, request, session, redirect, make_response
from pymysql import connect, cursors
from pymysql.err import MySQLError
import bcrypt

app = Flask(__name__)

flask_secret = os.getenv('FLASK_SECRET_KEY')
if not flask_secret:
    raise RuntimeError('FLASK_SECRET_KEY environment variable not set')
app.secret_key = flask_secret

db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_name = os.getenv('DB_NAME')
if not all([db_host, db_user, db_pass, db_name]):
    raise RuntimeError('Database environment variables DB_HOST, DB_USER, DB_PASS, DB_NAME must be set')

def get_db_connection():
    try:
        return connect(host=db_host, user=db_user, password=db_pass, database=db_name, cursorclass=cursors.DictCursor, autocommit=True)
    except MySQLError:
        raise RuntimeError('Database connection failed')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return make_response('Missing username or password', 400)
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute('SELECT password_hash FROM users WHERE username = %s', (username,))
            row = cur.fetchone()
        conn.close()
    except Exception:
        return make_response('Internal server error', 500)
    if not row or 'password_hash' not in row:
        return make_response('Incorrect username or password', 401)
    pw_hash = row['password_hash']
    if isinstance(pw_hash, str):
        pw_hash = pw_hash.encode('utf-8')
    if bcrypt.checkpw(password.encode('utf-8'), pw_hash):
        session['username'] = username
        return redirect('/session')
    return make_response('Incorrect username or password', 401)

@app.route('/session')
def session_info():
    user = session.get('username')
    if user:
        return f'Logged in as {user}'
    return make_response('Not logged in', 401)

if __name__ == '__main__':
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', '5000'))
    app.run(host=host, port=port)