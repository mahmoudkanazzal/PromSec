"""Note: In production, passwords should be hashed and verified with a secure algorithm."""
import os
from flask import Flask, request, session, redirect
import MySQLdb

app = Flask(__name__)
secret = os.getenv('FLASK_SECRET_KEY')
if not secret:
    raise RuntimeError('FLASK_SECRET_KEY environment variable not set')
app.secret_key = secret
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    db_host = os.getenv('DB_HOST')
    db_user = os.getenv('DB_USER')
    db_pass = os.getenv('DB_PASS')
    db_name = os.getenv('DB_NAME')
    try:
        with MySQLdb.connect(host=db_host, user=db_user, passwd=db_pass, db=db_name) as conn:
            with conn.cursor() as cur:
                cur.execute('SELECT * FROM users WHERE username=%s AND password=%s', (username, password))
                rows = cur.fetchall()
                if rows:
                    session['username'] = username
                    return redirect('/session')
                return 'Incorrect username or password'
    except Exception:
        return 'Incorrect username or password'

if __name__ == '__main__':
    app.run()