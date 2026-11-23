#!/usr/bin/env python3
import os
import sys
import logging
import bcrypt
import MySQLdb
from flask import Flask, request, make_response
from contextlib import closing

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

MAX_USERNAME_LENGTH = 255
MAX_PASSWORD_LENGTH = 255

def get_db_connection():
    host = os.getenv('DB_HOST', 'localhost')
    user = os.getenv('DB_USER', 'app_user')
    passwd = os.getenv('DB_PASS', '')
    db = os.getenv('DB_NAME', 'cwe200')
    ssl_ca = os.getenv('DB_SSL_CA')
    ssl_cert = os.getenv('DB_SSL_CERT')
    ssl_key = os.getenv('DB_SSL_KEY')
    ssl_params = {}
    if ssl_ca or ssl_cert or ssl_key:
        if ssl_ca:
            ssl_params['ca'] = ssl_ca
        if ssl_cert:
            ssl_params['cert'] = ssl_cert
        if ssl_key:
            ssl_params['key'] = ssl_key
    if ssl_params:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db,
                               charset='utf8mb4', use_unicode=True, ssl=ssl_params)
    else:
        conn = MySQLdb.connect(host=host, user=user, passwd=passwd, db=db,
                               charset='utf8mb4', use_unicode=True)
    return conn

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    if not username or not password:
        return 'false'
    if len(username) > MAX_USERNAME_LENGTH or len(password) > MAX_PASSWORD_LENGTH:
        return 'false'
    try:
        with closing(get_db_connection()) as conn:
            with closing(conn.cursor()) as cur:
                cur.execute('SELECT password FROM users WHERE username = %s', (username,))
                row = cur.fetchone()
                if not row:
                    return 'false'
                stored_hash = row[0]
                if isinstance(stored_hash, str):
                    stored_hash = stored_hash.encode('utf-8')
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
                    return 'true'
                else:
                    return 'false'
    except MySQLdb.Error as e:
        logger.error('Database error: %s', e)
        return 'false'
    except Exception as e:
        logger.error('Unexpected error: %s', e)
        return 'false'

if __name__ == '__main__':
    app.run()