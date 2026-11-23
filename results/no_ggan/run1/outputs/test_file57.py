#!/usr/bin/env python3
import os
import sys
import re
import time
import threading
import logging
import json
import bcrypt
import MySQLdb
from flask import Flask, request, jsonify

logging.basicConfig(stream=sys.stderr, level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'app_user')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME', 'cwe200')
DB_SSL_CA = os.getenv('DB_SSL_CA')
DB_SSL_CERT = os.getenv('DB_SSL_CERT')
DB_SSL_KEY = os.getenv('DB_SSL_KEY')
FLASK_SECRET_KEY = os.getenv('FLASK_SECRET_KEY')

missing = []
if not DB_PASSWORD:
    missing.append('DB_PASSWORD')
if not FLASK_SECRET_KEY:
    missing.append('FLASK_SECRET_KEY')
if missing:
    logger.error('Missing required environment variables: %s', ', '.join(missing))
    sys.exit(1)
if len(FLASK_SECRET_KEY) < 32:
    logger.error('FLASK_SECRET_KEY must be at least 32 characters')
    sys.exit(1)
ssl_vars = [DB_SSL_CA, DB_SSL_CERT, DB_SSL_KEY]
if any(ssl_vars) and not all(ssl_vars):
    logger.error('All of DB_SSL_CA, DB_SSL_CERT, DB_SSL_KEY must be set together')
    sys.exit(1)

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SECURE'] = True

_attempts = {}
_lock = threading.Lock()
_RATE_LIMIT = 5
_WINDOW = 60

def _prune_attempts(ip):
    now = time.time()
    with _lock:
        timestamps = _attempts.get(ip, [])
        _attempts[ip] = [t for t in timestamps if now - t < _WINDOW]

def _record_attempt(ip):
    now = time.time()
    with _lock:
        _attempts.setdefault(ip, []).append(now)

def _get_client_ip():
    return request.remote_addr

def get_db_connection():
    params = {
        'host': DB_HOST,
        'user': DB_USER,
        'passwd': DB_PASSWORD,
        'db': DB_NAME,
        'charset': 'utf8mb4',
        'autocommit': True
    }
    if all(ssl_vars):
        params['ssl'] = {
            'ca': DB_SSL_CA,
            'cert': DB_SSL_CERT,
            'key': DB_SSL_KEY
        }
    return MySQLdb.connect(**params)

_USERNAME_REGEX = re.compile(r'^[A-Za-z0-9_.-]{1,128}$')
_PASSWORD_REGEX = re.compile(r'^[\x20-\x7E]{1,128}$')

@app.route('/login', methods=['POST'])
def login():
    ip = _get_client_ip()
    _prune_attempts(ip)
    with _lock:
        if len(_attempts.get(ip, [])) >= _RATE_LIMIT:
            return jsonify({"error": "Too many login attempts"}), 429
    data = request.get_json(silent=True)
    if not data:
        data = request.form
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not _USERNAME_REGEX.fullmatch(username) or not _PASSWORD_REGEX.fullmatch(password):
        return jsonify({"result": False}), 400
    _record_attempt(ip)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        sql = "SELECT password FROM users WHERE username = %s"
        cursor.execute(sql, (username,))
        row = cursor.fetchone()
        if not row:
            return jsonify({"result": False})
        stored_hash = row[0]
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return jsonify({"result": True})
        else:
            return jsonify({"result": False})
    except MySQLdb.Error:
        logger.exception('Database error during login')
        return jsonify({"result": False}), 500
    finally:
        try:
            if cursor:
                cursor.close()
        except Exception:
            logger.exception('Error closing cursor')
        try:
            if conn:
                conn.close()
        except Exception:
            logger.exception('Error closing connection')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)