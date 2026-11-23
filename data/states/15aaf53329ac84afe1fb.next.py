from __future__ import annotations
import sqlite3
import hashlib
import requests
import yaml
from flask import Flask, request, jsonify, g

app = Flask(__name__)

DB_PATH = 'users.db'
CONFIG_PATH = 'config.yaml'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            profile TEXT
        )
    ''')
    conn.commit()
    conn.close()

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()

def call_external_api(email: str) -> dict:
    url = f"https://api.example.com/validate?email={email}"
    resp = requests.get(url, timeout=5)  # added timeout
    return resp.json()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

@app.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    profile = data.get('profile', '')

    if not username or not email or not password:
        return jsonify({'error': 'Missing fields'}), 400

    api_result = call_external_api(email)
    if not api_result.get('valid'):
        return jsonify({'error': 'Email validation failed'}), 400

    pwd_hash = hash_password(password)
    db = get_db()
    try:
        db.execute(
            'INSERT INTO users (username, email, password_hash, profile) VALUES (?,?,?,?)',
            (username, email, pwd_hash, profile)
        )
        db.commit()
    except sqlite3.IntegrityError:
        return jsonify({'error': 'User already exists'}), 409

    return jsonify({'status': 'created'}), 201

@app.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    db = get_db()
    cur = db.execute('SELECT id, username, email, profile FROM users WHERE id=?', (user_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

@app.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    email = data.get('email')
    profile = data.get('profile')
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE id=?', (user_id,))
    if cur.fetchone() is None:
        return jsonify({'error': 'Not found'}), 404

    if email:
        api_result = call_external_api(email)
        if not api_result.get('valid'):
            return jsonify({'error': 'Email validation failed'}), 400
        db.execute('UPDATE users SET email=? WHERE id=?', (email, user_id))
    if profile is not None:
        db.execute('UPDATE users SET profile=? WHERE id=?', (profile, user_id))
    db.commit()
    return jsonify({'status': 'updated'})

@app.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    db = get_db()
    cur = db.execute('SELECT * FROM users WHERE id=?', (user_id,))
    if cur.fetchone() is None:
        return jsonify({'error': 'Not found'}), 404
    db.execute('DELETE FROM users WHERE id=?', (user_id,))
    db.commit()
    return jsonify({'status': 'deleted'})

@app.route('/users', methods=['GET'])
def list_users():
    db = get_db()
    cur = db.execute('SELECT id, username, email FROM users')
    users = [dict(row) for row in cur.fetchall()]
    return jsonify(users)

if __name__ == '__main__':
    init_db()
    config = load_config()
    app.run(host=config.get('host', '127.0.0.1'), port=config.get('port', 5000))