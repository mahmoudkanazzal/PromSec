from __future__ import annotations
import sqlite3
import hashlib
import os
from flask import Flask, request, jsonify, g

app = Flask(__name__)

def open_connection(db_path: str = 'users.db', password: str = None) -> sqlite3.Connection:
    # password argument is ignored in this quick implementation
    return sqlite3.connect(db_path)

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = open_connection(db_path='users.db')
    return g.db

def init_db() -> None:
    conn = sqlite3.connect('users.db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        bio TEXT,
        pwd_hash TEXT
    )''')
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def create_user(username: str, name: str, email: str, bio: str, password: str) -> bool:
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    db = get_db()
    try:
        db.execute(
            'INSERT INTO users (username, name, email, bio, pwd_hash) VALUES (?,?,?,?,?)',
            (username, name, email, bio, pwd_hash)
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def get_user(username: str) -> dict | None:
    db = get_db()
    cur = db.execute(
        'SELECT username, name, email, bio, pwd_hash FROM users WHERE username=?',
        (username,)
    )
    row = cur.fetchone()
    if row:
        return {
            'username': row[0],
            'name': row[1],
            'email': row[2],
            'bio': row[3],
            'pwd_hash': row[4]
        }
    return None

def update_user(username: str, name: str, email: str, bio: str) -> None:
    db = get_db()
    db.execute(
        'UPDATE users SET name=?, email=?, bio=? WHERE username=?',
        (name, email, bio, username)
    )
    db.commit()

def login_service(username: str, password: str = None) -> bool:
    if password is None:
        return False
    user = get_user(username)
    if not user:
        return False
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    return pwd_hash == user['pwd_hash']

@app.route('/create', methods=['POST'])
def create():
    data = request.get_json()
    required = {'username', 'name', 'email', 'bio', 'password'}
    if not data or not required.issubset(data):
        return jsonify({'error': 'missing fields'}), 400
    ok = create_user(
        data['username'],
        data['name'],
        data['email'],
        data['bio'],
        data['password']
    )
    if not ok:
        return jsonify({'error': 'user exists'}), 409
    return jsonify({'status': 'created'}), 201

@app.route('/profile/<username>', methods=['GET'])
def profile(username):
    user = get_user(username)
    if not user:
        return jsonify({'error': 'not found'}), 404
    user.pop('pwd_hash')
    return jsonify(user)

@app.route('/profile/<username>', methods=['POST'])
def edit(username):
    data = request.get_json()
    user = get_user(username)
    if not user:
        return jsonify({'error': 'not found'}), 404
    name = data.get('name', user['name'])
    email = data.get('email', user['email'])
    bio = data.get('bio', user['bio'])
    update_user(username, name, email, bio)
    return jsonify({'status': 'updated'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'missing credentials'}), 400
    if login_service(data['username'], password=data['password']):
        return jsonify({'status': 'ok'})
    return jsonify({'status': 'fail'}), 401

if __name__ == '__main__':
    init_db()
    app.run(debug=False)