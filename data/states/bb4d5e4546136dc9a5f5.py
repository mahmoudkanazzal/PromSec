from __future__ import annotations
import os
import sqlite3
import hashlib
import json
import yaml
import requests
import tempfile
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)
DB_PATH = 'users.db'

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT,
            email TEXT,
            profile TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_db() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)

def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

def create_user(username: str, password: str, email: str, profile: dict) -> int:
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO users (username, password, email, profile) VALUES (?,?,?,?)',
        (username, hash_password(password), email, yaml.dump(profile))
    )
    conn.commit()
    uid = cur.lastrowid
    conn.close()
    return uid

def get_user(uid: int) -> dict | None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT id, username, email, profile FROM users WHERE id=?', (uid,))
    row = cur.fetchone()
    conn.close()
    if row:
        return {
            'id': row[0],
            'username': row[1],
            'email': row[2],
            'profile': yaml.safe_load(row[3])
        }
    return None

def update_user(uid: int, data: dict) -> bool:
    conn = get_db()
    cur = conn.cursor()
    fields = []
    values = []
    if 'username' in data:
        fields.append('username=?')
        values.append(data['username'])
    if 'password' in data:
        fields.append('password=?')
        values.append(hash_password(data['password']))
    if 'email' in data:
        fields.append('email=?')
        values.append(data['email'])
    if 'profile' in data:
        fields.append('profile=?')
        values.append(yaml.dump(data['profile']))
    if not fields:
        return False
    values.append(uid)
    sql = 'UPDATE users SET ' + ', '.join(fields) + ' WHERE id=?'
    cur.execute(sql, tuple(values))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed

def delete_user(uid: int) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM users WHERE id=?', (uid,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted

def write_temp_profile(uid: int, profile: dict) -> str:
    fd, path = tempfile.mkstemp(prefix=f'user_{uid}_profile_', suffix='.pkl')
    with os.fdopen(fd, 'w') as f:
        json.dump(profile, f)
    return path

def read_temp_profile(path: str) -> dict:
    with open(path, 'r') as f:
        return json.load(f)

@app.route('/users', methods=['POST'])
def api_create_user():
    data = request.json or {}
    uid = create_user(
        username=data.get('username', ''),
        password=data.get('password', ''),
        email=data.get('email', ''),
        profile=data.get('profile', {})
    )
    return jsonify({'id': uid}), 201

@app.route('/users/<int:uid>', methods=['GET'])
def api_get_user(uid):
    user = get_user(uid)
    if not user:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(user)

@app.route('/users/<int:uid>', methods=['PUT'])
def api_update_user(uid):
    data = request.json or {}
    success = update_user(uid, data)
    if not success:
        return jsonify({'error': 'Update failed'}), 400
    return jsonify({'status': 'updated'})

@app.route('/users/<int:uid>', methods=['DELETE'])
def api_delete_user(uid):
    success = delete_user(uid)
    if not success:
        return jsonify({'error': 'Delete failed'}), 400
    return jsonify({'status': 'deleted'})

@app.route('/users/<int:uid>/export', methods=['GET'])
def api_export_user(uid):
    user = get_user(uid)
    if not user:
        return jsonify({'error': 'Not found'}), 404
    path = write_temp_profile(uid, user['profile'])
    return send_file(path, as_attachment=True, download_name=f'user_{uid}_profile.pkl')

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)