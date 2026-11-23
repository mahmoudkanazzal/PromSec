from flask import Flask, request, redirect, session
from os import getenv
import mysql.connector
import logging
from werkzeug.security import check_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

flask_secret = getenv('FLASK_SECRET_KEY')
if not flask_secret:
    raise RuntimeError('Environment variable FLASK_SECRET_KEY is required')
app = Flask(__name__)
app.secret_key = flask_secret
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = True

db_host = getenv('DB_HOST')
db_user = getenv('DB_USER')
db_pass = getenv('DB_PASS')
db_name = getenv('DB_NAME')
if not all([db_host, db_user, db_pass, db_name]):
    raise RuntimeError('Database connection environment variables DB_HOST, DB_USER, DB_PASS, DB_NAME are required')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    conn = None
    cur = None
    try:
        conn = mysql.connector.connect(host=db_host, user=db_user, password=db_pass, database=db_name)
        cur = conn.cursor()
        cur.execute('SELECT id, role, password FROM users WHERE username = %s', (username,))
        row = cur.fetchone()
        if row and check_password_hash(row[2], password):
            session['id'] = row[0]
            session['Role'] = row[1]
            return redirect('/dashboard')
        return redirect('/login')
    except Exception:
        logger.exception('Error during login')
        return redirect('/login')
    finally:
        if cur:
            try:
                cur.close()
            except Exception:
                logger.exception('Error closing cursor')
        if conn:
            try:
                conn.close()
            except Exception:
                logger.exception('Error closing connection')

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)