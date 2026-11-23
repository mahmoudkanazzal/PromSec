from __future__ import annotations

import os
import yaml
import sqlite3
import subprocess
import hashlib
import json
import requests
from flask import Flask, request, jsonify

APP = Flask(__name__)
CONFIG = {}
DB_PATH = 'microservice.db'

def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        cfg = yaml.safe_load(f)
    return cfg

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value BLOB
        )
    ''')
    conn.commit()
    conn.close()

def save_setting(key: str, value: any) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    # Store data as JSON to avoid unsafe pickle deserialization
    blob = json.dumps(value)
    cur.execute('REPLACE INTO settings (key, value) VALUES (?, ?)', (key, blob))
    conn.commit()
    conn.close()

def get_setting(key: str) -> any:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT value FROM settings WHERE key=?', (key,))
    row = cur.fetchone()
    conn.close()
    if row:
        # Load data from JSON safely
        return json.loads(row[0])
    return None

def compute_hash(data: bytes) -> str:
    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()

def run_user_command(user_input: str) -> dict:
    # Use list form to avoid shell injection
    result = subprocess.run(['echo', user_input], capture_output=True, text=True)
    return {
        'command': f"echo {user_input}",
        'returncode': result.returncode,
        'stdout': result.stdout.strip(),
        'stderr': result.stderr.strip()
    }

@APP.route('/config', methods=['GET'])
def get_config():
    return jsonify(CONFIG)

@APP.route('/run', methods=['POST'])
def run():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'missing command'}), 400
    user_cmd = data['command']
    exec_result = run_user_command(user_cmd)
    save_setting('last_command', exec_result)
    return jsonify(exec_result)

def main():
    global CONFIG
    config_path = os.getenv('MICRO_CFG', 'config.yaml')
    if os.path.exists(config_path):
        CONFIG = load_config(config_path)
    init_db()
    APP.run(host='127.0.0.1', port=CONFIG.get('port', 5000))

if __name__ == '__main__':
    main()