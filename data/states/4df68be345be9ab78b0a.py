from __future__ import annotations
import os
import json
import sqlite3
import requests
from flask import Flask, request, jsonify, abort

CONFIG_DB = 'config.db'
CACHE_FILE = 'config_cache.json'
REMOTE_CONFIG_URL = os.getenv('REMOTE_CONFIG_URL', 'http://localhost:5001/config')
app = Flask(__name__)

def init_db() -> None:
    conn = sqlite3.connect(CONFIG_DB)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS config (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

def load_config_from_file(path: str) -> dict:
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("Config file must contain a mapping")
    return data

def fetch_remote_config() -> dict:
    resp = requests.get(REMOTE_CONFIG_URL, timeout=5)
    if resp.status_code != 200:
        raise RuntimeError("Failed to fetch remote config")
    data = resp.json()
    if not isinstance(data, dict):
        raise ValueError("Remote config must be a dict")
    return data

def save_config_to_db(config: dict) -> None:
    conn = sqlite3.connect(CONFIG_DB)
    c = conn.cursor()
    for k, v in config.items():
        c.execute('REPLACE INTO config (key, value) VALUES (?, ?)', (k, str(v)))
    conn.commit()
    conn.close()

def load_config_from_db() -> dict:
    conn = sqlite3.connect(CONFIG_DB)
    c = conn.cursor()
    c.execute('SELECT key, value FROM config')
    rows = c.fetchall()
    conn.close()
    return {k: v for k, v in rows}

def cache_config(config: dict) -> None:
    with open(CACHE_FILE, 'w') as f:
        json.dump(config, f)

def load_cached_config() -> dict | None:
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, 'r') as f:
        return json.load(f)

def get_config() -> dict:
    cached = load_cached_config()
    if cached is not None:
        return cached
    try:
        cfg = fetch_remote_config()
    except Exception:
        cfg = load_config_from_file('config.yaml')
    save_config_to_db(cfg)
    cache_config(cfg)
    return cfg

def _require_admin() -> None:
    token = request.headers.get('Authorization')
    if token is None:
        abort(401, description="Missing auth token")
    user = token.split()[-1]
    if user != 'admin':
        abort(403, description="Permission denied")

@app.route('/config', methods=['GET'])
def config_endpoint():
    _require_admin()
    cfg = get_config()
    return jsonify(cfg)

def reload_service() -> str:
    # Simulate a reload operation without invoking an external process
    return "reloading"

@app.route('/reload', methods=['POST'])
def reload_endpoint():
    _require_admin()
    msg = reload_service()
    return jsonify({'status': 'reloaded', 'msg': msg})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=8000)