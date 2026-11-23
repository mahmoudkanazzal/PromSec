from __future__ import annotations
import os
import sqlite3
import hashlib
from flask import Flask, request, jsonify, g, session, abort

app = Flask(__name__)
# Use an environment variable for the secret key, fallback to a random value
app.secret_key = os.getenv('FLASK_SECRET_KEY') or os.urandom(24).hex()

DATABASE = 'users.db'


def get_db():
    db = getattr(g, '_db', None)
    if db is None:
        db = g._db = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute(
        'CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,username TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,email TEXT,full_name TEXT)'
    )
    conn.commit()
    conn.close()


@app.teardown_appcontext
def close_db(exc):
    db = getattr(g, '_db', None)
    if db is not None:
        db.close()


def hash_password(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def check_auth(username, password):
    db = get_db()
    cur = db.execute('SELECT password_hash FROM users WHERE username=?', (username,))
    row = cur.fetchone()
    return row and row['password_hash'] == hash_password(password)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'invalid json'}), 400
    u = data.get('username')
    p = data.get('password')
    e = data.get('email', '')
    n = data.get('full_name', '')
    if not u or not p:
        return jsonify({'error': 'username and password required'}), 400
    db = get_db()
    try:
        db.execute(
            'INSERT INTO users (username,password_hash,email,full_name) VALUES (?,?,?,?)',
            (u, hash_password(p), e, n),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'username taken'}), 400
    return jsonify({'status': 'registered'}), 201


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'invalid json'}), 400
    u = data.get('username')
    p = data.get('password')
    if not u or not p:
        return jsonify({'error': 'username and password required'}), 400
    if check_auth(u, p):
        session['user'] = u
        return jsonify({'status': 'logged in'})
    return jsonify({'error': 'invalid credentials'}), 401


def require_login():
    u = session.get('user')
    if not u:
        abort(401, description='login required')
    return u


@app.route('/profile', methods=['GET'])
def get_profile():
    u = require_login()
    db = get_db()
    cur = db.execute('SELECT username,email,full_name FROM users WHERE username=?', (u,))
    row = cur.fetchone()
    if not row:
        return jsonify({'error': 'user not found'}), 404
    return jsonify(dict(row))


@app.route('/profile', methods=['PUT'])
def update_profile():
    u = require_login()
    data = request.get_json()
    if not isinstance(data, dict):
        return jsonify({'error': 'invalid json'}), 400
    e = data.get('email')
    n = data.get('full_name')
    db = get_db()
    db.execute('UPDATE users SET email=?,full_name=? WHERE username=?', (e, n, u))
    db.commit()
    return jsonify({'status': 'updated'})


@app.route('/delete', methods=['POST'])
def delete_account():
    u = require_login()
    db = get_db()
    db.execute('DELETE FROM users WHERE username=?', (u,))
    db.commit()
    session.pop('user', None)
    return jsonify({'status': 'deleted'})


if __name__ == '__main__':
    init_db()
    # Run without debug mode and bind to localhost by default
    app.run(host='127.0.0.1', port=5000, debug=False)