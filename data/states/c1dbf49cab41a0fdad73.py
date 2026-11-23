from __future__ import annotations
import os
import sqlite3
from flask import Flask, request, jsonify, g

# Retrieve admin password from environment variable instead of hardcoding
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')
if ADMIN_PASSWORD is None:
    raise RuntimeError('ADMIN_PASSWORD environment variable not set')

app = Flask(__name__)

def init_db() -> None:
    db = sqlite3.connect('users.db')
    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    db.commit()
    db.close()

def get_db() -> sqlite3.Connection:
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect('users.db')
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e=None) -> None:
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()

def create_user(username: str, email: str) -> None:
    db = get_db()
    db.execute('INSERT INTO users (username, email) VALUES (?, ?)', (username, email))
    db.commit()

def get_user(username: str) -> sqlite3.Row | None:
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cur.fetchone()

def verify_password(pw: str) -> bool:
    return pw == ADMIN_PASSWORD

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    username = data.get('username')
    email = data.get('email')
    if not username or not email:
        return jsonify({'error': 'missing fields'}), 400
    try:
        create_user(username, email)
    except sqlite3.IntegrityError:
        return jsonify({'error': 'user exists'}), 409
    return jsonify({'status': 'created'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    password = data.get('password')
    if verify_password(password):
        return jsonify({'status': 'logged in'}), 200
    return jsonify({'error': 'invalid password'}), 401

@app.route('/profile/<username>', methods=['GET'])
def profile(username: str):
    user = get_user(username)
    if not user:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'id': user['id'], 'username': user['username'], 'email': user['email']}), 200

app.teardown_appcontext(close_db)

if __name__ == '__main__':
    if not os.path.exists('users.db'):
        init_db()
    # Bind to localhost to avoid exposing the service on all interfaces
    app.run(host='127.0.0.1', port=5000)