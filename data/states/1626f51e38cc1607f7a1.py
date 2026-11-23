from __future__ import annotations
import sqlite3
import pickle
import yaml
import hashlib
import requests
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
DB_PATH = 'config.db'


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS configs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            data BLOB NOT NULL,
            checksum TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()


def compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def save_config(name: str, config_obj: object) -> None:
    data = pickle.dumps(config_obj)
    checksum = compute_checksum(data)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT OR REPLACE INTO configs (name, data, checksum)
        VALUES (?, ?, ?)
    ''', (name, data, checksum))
    conn.commit()
    conn.close()


def load_config(name: str) -> object | None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT data, checksum FROM configs WHERE name = ?', (name,))
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    data, stored_checksum = row
    if compute_checksum(data) != stored_checksum:
        return None
    return pickle.loads(data)


def load_yaml_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def fetch_remote_config(url: str) -> dict:
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()


@app.route('/config/<name>', methods=['GET'])
def get_config(name: str):
    cfg = load_config(name)
    if cfg is None:
        abort(404)
    return jsonify({'name': name, 'config': cfg})


@app.route('/config/<name>', methods=['POST'])
def set_config(name: str):
    if not request.data:
        abort(400)
    try:
        config_obj = pickle.loads(request.data)
    except Exception:
        abort(400)
    save_config(name, config_obj)
    return jsonify({'status': 'saved'}), 201


@app.route('/load_yaml', methods=['POST'])
def load_yaml():
    payload = request.get_json()
    if not payload or 'path' not in payload:
        abort(400)
    cfg = load_yaml_config(payload['path'])
    return jsonify(cfg)


@app.route('/fetch_remote', methods=['POST'])
def fetch_remote():
    payload = request.get_json()
    if not payload or 'url' not in payload:
        abort(400)
    cfg = fetch_remote_config(payload['url'])
    return jsonify(cfg)


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)