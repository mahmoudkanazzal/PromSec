import os
from flask import Flask, request, session, redirect, url_for, make_response
import MySQLdb
import bcrypt
from contextlib import closing

flask_secret = os.getenv('FLASK_SECRET_KEY')
if not flask_secret:
    raise RuntimeError('Environment variable FLASK_SECRET_KEY is required')
db_host = os.getenv('DB_HOST')
db_user = os.getenv('DB_USER')
db_pass = os.getenv('DB_PASS')
db_name = os.getenv('DB_NAME')
missing = [n for n, v in (('DB_HOST', db_host), ('DB_USER', db_user), ('DB_PASS', db_pass), ('DB_NAME', db_name)) if not v]
if missing:
    raise RuntimeError('Missing environment variables: ' + ', '.join(missing))

app = Flask(__name__)
app.secret_key = flask_secret

def get_connection():
    return MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name, charset='utf8mb4', use_unicode=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return '''
        <form method="post">
        Username: <input name="username"><br>
        Password: <input name="password" type="password"><br>
        <input type="submit" value="Login">
        </form>
        '''
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return make_response('Invalid credentials', 401)
    try:
        with closing(get_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT password_hash FROM users WHERE username=%s', (username,))
                row = cur.fetchone()
                if not row:
                    return make_response('Invalid credentials', 401)
                stored_hash = row[0]
                if isinstance(stored_hash, bytes):
                    stored_hash = stored_hash.decode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    session['username'] = username
                    return redirect(url_for('session_info'))
                return make_response('Invalid credentials', 401)
    except MySQLdb.Error:
        return make_response('Invalid credentials', 401)
    except Exception:
        return make_response('Invalid credentials', 401)

@app.route('/session')
def session_info():
    username = session.get('username')
    if not username:
        return redirect(url_for('login'))
    return f'Logged in as {username}'

if __name__ == '__main__':
    app.run()