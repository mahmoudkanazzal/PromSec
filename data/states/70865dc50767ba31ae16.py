from __future__ import annotations
import os, subprocess, hashlib, pickle
import yaml, sqlite3, requests
from flask import Flask, request, jsonify

CONFIG_DB = 'config.db'
CACHE_FILE = 'config_cache.pkl'
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
    assert isinstance(data, dict), "Config file must contain a mapping"
    return data

def fetch_remote_config() -> dict:
    resp = requests.get(REMOTE_CONFIG_URL, timeout=5)
    assert resp.status_code == 200, "Failed to fetch remote config"
    data = resp.json()
    assert isinstance(data, dict), "Remote config must be a dict"
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
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(config, f)

def load_cached_config() -> dict | None:
    if not os.path.exists(CACHE_FILE):
        return None
    with open(CACHE_FILE, 'rb') as f:
        return pickle.load(f)

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

@app.route('/config', methods=['GET'])
def config_endpoint():
    token = request.headers.get('Authorization')
    assert token is not None, "Missing auth token"
    user = token.split()[-1]
    assert user == 'admin', "Permission denied"
    cfg = get_config()
    return jsonify(cfg)

def reload_service():
    result = subprocess.run(['echo', 'reloading'], capture_output=True, text=True)
    assert result.returncode == 0, "Reload failed"
    return result.stdout.strip()

@app.route('/reload', methods=['POST'])
def reload_endpoint():
    token = request.headers.get('Authorization')
    assert token is not None, "Missing auth token"
    user = token.split()[-1]
    assert user == 'admin', "Permission denied"
    msg = reload_service()
    return jsonify({'status': 'reloaded', 'msg': msg})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=8000)