from __future__ import annotations
import os
import sqlite3
import hashlib
from flask import Flask, request, jsonify, g

DB_PATH = os.path.join(os.path.dirname(__file__), 'users.db')


def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            full_name TEXT,
            email TEXT,
            password_hash TEXT
        )
    ''')
    conn.commit()
    conn.close()


def hash_password(pwd: str) -> str:
    return hashlib.sha256(pwd.encode('utf-8')).hexdigest()


def create_user(username: str, full_name: str, email: str, password: str) -> bool:
    db = get_db()
    pwd_hash = hash_password(password)
    try:
        db.execute(
            "INSERT INTO users (username, full_name, email, password_hash) VALUES (?, ?, ?, ?)",
            (username, full_name, email, pwd_hash),
        )
        db.commit()
        return True
    except sqlite3.IntegrityError:
        return False


def get_user(username: str):
    db = get_db()
    cur = db.execute(
        "SELECT username, full_name, email FROM users WHERE username = ?", (username,)
    )
    row = cur.fetchone()
    return dict(row) if row else None


def update_user(
    username: str, full_name: str = None, email: str = None, password: str = None
) -> bool:
    db = get_db()
    parts = []
    params = []
    if full_name is not None:
        parts.append("full_name = ?")
        params.append(full_name)
    if email is not None:
        parts.append("email = ?")
        params.append(email)
    if password is not None:
        pwd_hash = hash_password(password)
        parts.append("password_hash = ?")
        params.append(pwd_hash)
    if not parts:
        return False
    set_clause = ", ".join(parts)
    params.append(username)
    db.execute(f"UPDATE users SET {set_clause} WHERE username = ?", tuple(params))
    db.commit()
    return db.total_changes > 0


def delete_user(username: str) -> bool:
    db = get_db()
    db.execute("DELETE FROM users WHERE username = ?", (username,))
    db.commit()
    return db.total_changes > 0


def list_users():
    db = get_db()
    cur = db.execute("SELECT username, full_name, email FROM users")
    return [dict(row) for row in cur.fetchall()]


def create_app() -> Flask:
    app = Flask(__name__)
    app.teardown_appcontext(close_db)

    @app.route('/users', methods=['POST'])
    def api_create_user():
        data = request.json or {}
        if not all(k in data for k in ('username', 'full_name', 'email', 'password')):
            return jsonify({'error': 'Missing fields'}), 400
        success = create_user(
            data['username'], data['full_name'], data['email'], data['password']
        )
        if success:
            return jsonify({'status': 'created'}), 201
        else:
            return jsonify({'error': 'User exists'}), 409

    @app.route('/users/<username>', methods=['GET'])
    def api_get_user(username):
        user = get_user(username)
        if user:
            return jsonify(user)
        else:
            return jsonify({'error': 'Not found'}), 404

    @app.route('/users/<username>', methods=['PUT'])
    def api_update_user(username):
        data = request.json or {}
        if not data:
            return jsonify({'error': 'No data'}), 400
        success = update_user(
            username,
            full_name=data.get('full_name'),
            email=data.get('email'),
            password=data.get('password'),
        )
        if success:
            return jsonify({'status': 'updated'})
        else:
            return jsonify({'error': 'Update failed'}), 400

    @app.route('/users/<username>', methods=['DELETE'])
    def api_delete_user(username):
        success = delete_user(username)
        if success:
            return jsonify({'status': 'deleted'})
        else:
            return jsonify({'error': 'Delete failed'}), 400

    @app.route('/users', methods=['GET'])
    def api_list_users():
        users = list_users()
        return jsonify(users)

    return app


if __name__ == '__main__':
    init_db()
    app = create_app()
    app.run(host='127.0.0.1', port=5000)