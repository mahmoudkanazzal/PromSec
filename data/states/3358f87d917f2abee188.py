from __future__ import annotations
import sqlite3
import hashlib
from flask import Flask, request, session, jsonify, g
import os

DATABASE = 'users.db'
app = Flask(__name__)

# Use an environment variable for the secret key, fallback to a random value
_secret_key = os.getenv('FLASK_SECRET_KEY')
if _secret_key:
    app.secret_key = _secret_key
else:
    app.secret_key = os.urandom(32)


def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db() -> None:
    conn = get_db()
    conn.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )''')
    conn.commit()


def hash_password(password: str) -> str:
    # Use SHA-256 instead of MD5 for password hashing
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def add_user(username: str, password: str) -> bool:
    try:
        conn = get_db()
        conn.execute('INSERT INTO users (username, password_hash) VALUES (?, ?)',
                     (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(username: str) -> sqlite3.Row | None:
    conn = get_db()
    cur = conn.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cur.fetchone()


def verify_user(username: str, password: str) -> bool:
    user = get_user(username)
    if user is None:
        return False
    return user['password_hash'] == hash_password(password)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': 'Missing fields'}), 400
    if add_user(username, password):
        return jsonify({'status': 'registered'}), 201
    else:
        return jsonify({'error': 'User exists'}), 409


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    username = data.get('username', '')
    password = data.get('password', '')
    if verify_user(username, password):
        session['user'] = username
        return jsonify({'status': 'logged in'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user', None)
    return jsonify({'status': 'logged out'}), 200


@app.route('/profile', methods=['GET'])
def profile():
    username = session.get('user')
    if not username:
        return jsonify({'error': 'Unauthorized'}), 401
    user = get_user(username)
    return jsonify({'username': user['username']}), 200


if __name__ == '__main__':
    if not os.path.exists(DATABASE):
        with app.app_context():
            init_db()
    # Bind to localhost to avoid exposing the service on all interfaces
    app.run(host='127.0.0.1', port=5000)