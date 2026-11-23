from __future__ import annotations
import base64
import hashlib
import json
import sqlite3
import yaml
import requests
from flask import Flask, request, jsonify, g

app = Flask(__name__)
DB_PATH = 'profiles.db'

def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
    return db

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            username TEXT PRIMARY KEY,
            data BLOB NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_username(username: str) -> str:
    return hashlib.sha256(username.encode()).hexdigest()

def store_profile(username: str, payload: bytes) -> None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('REPLACE INTO profiles (username, data) VALUES (?, ?)', (username, payload))
    conn.commit()

def load_profile(username: str) -> object | None:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT data FROM profiles WHERE username = ?', (username,))
    row = cur.fetchone()
    if row:
        try:
            return json.loads(row[0].decode('utf-8'))
        except Exception:
            return None
    return None

def delete_profile(username: str) -> bool:
    conn = get_db()
    cur = conn.cursor()
    cur.execute('DELETE FROM profiles WHERE username = ?', (username,))
    conn.commit()
    return cur.rowcount > 0

@app.route('/profile', methods=['POST'])
def create_or_update():
    username = request.form.get('username')
    payload_b64 = request.form.get('payload')
    if not username or not payload_b64:
        return jsonify({'error': 'missing fields'}), 400
    try:
        payload = base64.b64decode(payload_b64)
        json.loads(payload.decode('utf-8'))  # validate JSON
    except Exception:
        return jsonify({'error': 'invalid payload'}), 400
    store_profile(username, payload)
    return jsonify({'status': 'saved', 'hash': hash_username(username)})

@app.route('/profile/<username>', methods=['GET'])
def get_profile(username: str):
    profile = load_profile(username)
    if profile is None:
        return jsonify({'error': 'not found'}), 404
    return jsonify({'username': username, 'profile': profile})

@app.route('/profile/<username>', methods=['DELETE'])
def remove_profile(username: str):
    if delete_profile(username):
        return jsonify({'status': 'deleted'})
    return jsonify({'error': 'not found'}), 404

@app.route('/external', methods=['GET'])
def external():
    url = request.args.get('url')
    if not url:
        return jsonify({'error': 'url required'}), 400
    try:
        resp = requests.get(url, timeout=5)
        data = yaml.safe_load(resp.text)
    except Exception:
        return jsonify({'error': 'failed to fetch'}), 502
    return jsonify({'fetched': data})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)