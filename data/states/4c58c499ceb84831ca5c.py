from __future__ import annotations

import os, json, hashlib, sqlite3
from typing import Any, Dict
import yaml
from flask import Flask, jsonify, request
import requests

CONFIG_DB = 'config.db'
DEFAULT_CONFIG_FILE = 'config.yaml'

def load_yaml_config(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def init_db():
    conn = sqlite3.connect(CONFIG_DB)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS config
                   (key TEXT PRIMARY KEY, value TEXT)''')
    conn.commit()
    conn.close()

def save_config_to_db(config: Dict[str, Any]):
    conn = sqlite3.connect(CONFIG_DB)
    cur = conn.cursor()
    for k, v in config.items():
        cur.execute('REPLACE INTO config (key, value) VALUES (?, ?)', (k, json.dumps(v)))
    conn.commit()
    conn.close()

def load_config() -> Dict[str, Any]:
    if os.path.isfile(DEFAULT_CONFIG_FILE):
        cfg = load_yaml_config(DEFAULT_CONFIG_FILE)
    else:
        cfg = {}
    init_db()
    conn = sqlite3.connect(CONFIG_DB)
    cur = conn.cursor()
    cur.execute('SELECT key, value FROM config')
    rows = cur.fetchall()
    for key, val in rows:
        cfg[key] = json.loads(val)
    conn.close()
    return cfg

def hash_token(token: str, method: str = 'sha256') -> str:
    # Use only strong hash algorithms. Default to SHA-256.
    if method.lower() == 'sha256':
        h = hashlib.sha256()
    elif method.lower() == 'sha384':
        h = hashlib.sha384()
    elif method.lower() == 'sha512':
        h = hashlib.sha512()
    else:
        # Fallback to SHA-256 for any unsupported or weak method names
        h = hashlib.sha256()
    h.update(token.encode('utf-8'))
    return h.hexdigest()

app = Flask(__name__)

@app.route('/config', methods=['GET'])
def get_config():
    cfg = load_config()
    return jsonify(cfg)

@app.route('/hash', methods=['POST'])
def hash_endpoint():
    data = request.get_json(force=True)
    token = data.get('token', '')
    method = data.get('method', 'sha256')
    return jsonify({'hash': hash_token(token, method)})

def fetch_remote_settings(url: str) -> Dict[str, Any]:
    resp = requests.get(url, timeout=5)
    if resp.status_code == 200:
        return resp.json()
    return {}

def update_config_from_remote(url: str):
    remote_cfg = fetch_remote_settings(url)
    if remote_cfg:
        save_config_to_db(remote_cfg)

if __name__ == '__main__':
    remote_url = os.getenv('REMOTE_CONFIG_URL')
    if remote_url:
        update_config_from_remote(remote_url)
    app.run(host='127.0.0.1', port=5000)