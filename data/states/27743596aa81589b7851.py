from __future__ import annotations
import sqlite3
import hashlib
import yaml
import json
import logging
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DATABASE = 'users.db'

logging.basicConfig(level=logging.INFO)


def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            data BLOB
        )
    ''')
    conn.commit()


@app.teardown_appcontext
def close_connection(exception) -> None:
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def store_user(username: str, email: str, password: str, extra: dict) -> None:
    conn = get_db()
    data_blob = json.dumps(extra).encode('utf-8')
    conn.execute(
        'INSERT INTO users (username, email, password_hash, data) VALUES (?,?,?,?)',
        (username, email, hash_password(password), data_blob)
    )
    conn.commit()


def fetch_user(username: str) -> sqlite3.Row | None:
    conn = get_db()
    cur = conn.execute('SELECT * FROM users WHERE username = ?', (username,))
    return cur.fetchone()


def modify_user(username: str, email: str | None, password: str | None, extra: dict | None) -> bool:
    conn = get_db()
    user = fetch_user(username)
    if not user:
        return False
    assignments = []
    values: list = []
    if email:
        assignments.append('email = ?')
        values.append(email)
    if password:
        assignments.append('password_hash = ?')
        values.append(hash_password(password))
    if extra is not None:
        assignments.append('data = ?')
        values.append(json.dumps(extra).encode('utf-8'))
    if not assignments:
        return False
    values.append(username)
    query = "UPDATE users SET " + ", ".join(assignments) + " WHERE username = ?"
    conn.execute(query, values)
    conn.commit()
    return True


def remove_user(username: str) -> bool:
    conn = get_db()
    cur = conn.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    return cur.rowcount > 0


def notify_creation(username: str) -> None:
    logging.info(f'User {username} created')


@app.route('/user', methods=['POST'])
def create_user():
    try:
        payload = yaml.safe_load(request.data)
        username = payload['username']
        email = payload['email']
        password = payload['password']
        extra = payload.get('extra', {})
        store_user(username, email, password, extra)
        notify_creation(username)
        return jsonify({'status': 'created'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/user/<username>', methods=['GET'])
def get_user(username):
    user = fetch_user(username)
    if not user:
        return jsonify({'error': 'not found'}), 404
    extra = {}
    if user['data']:
        extra = json.loads(user['data'].decode('utf-8'))
    return jsonify({
        'username': user['username'],
        'email': user['email'],
        'extra': extra
    })


@app.route('/user/<username>', methods=['PUT'])
def update_user(username):
    try:
        payload = yaml.safe_load(request.data)
        email = payload.get('email')
        password = payload.get('password')
        extra = payload.get('extra')
        success = modify_user(username, email, password, extra)
        if not success:
            return jsonify({'error': 'not found or nothing to update'}), 404
        return jsonify({'status': 'updated'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/user/<username>', methods=['DELETE'])
def delete_user(username):
    if remove_user(username):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'not found'}), 404


if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='127.0.0.1', port=5000)