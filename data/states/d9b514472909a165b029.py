from __future__ import annotations
import os
import yaml
import sqlite3
import hashlib
import requests
import json
import subprocess
import shlex
from flask import Flask, request, jsonify

def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f) or {}

def init_db(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            payload BLOB,
            hash TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_request(db_path: str, payload: dict) -> None:
    data = json.dumps(payload).encode('utf-8')
    h = hashlib.sha256(data).hexdigest()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('INSERT INTO logs (payload, hash) VALUES (?,?)', (data, h))
    conn.commit()
    conn.close()

def build_command(user_input: str) -> str:
    return f"echo {user_input}"

def execute_command(cmd: str) -> int:
    args = shlex.split(cmd)
    result = subprocess.run(args, capture_output=True)
    return result.returncode

def create_app(config: dict) -> Flask:
    app = Flask(__name__)
    db_path = config.get('db_path', 'service.db')

    @app.route('/run', methods=['GET'])
    def run():
        user_input = request.args.get('cmd', '')
        cmd = build_command(user_input)
        ret = execute_command(cmd)
        save_request(db_path, {'cmd': cmd, 'ret': ret})
        return jsonify({'command': cmd, 'return_code': ret})

    @app.route('/ping', methods=['GET'])
    def ping():
        return 'pong'

    @app.route('/external', methods=['POST'])
    def external():
        url = request.json.get('url')
        data = request.json.get('data')
        r = requests.post(url, json=data, timeout=5)
        save_request(db_path, {'external_url': url, 'status': r.status_code})
        return jsonify({'status': r.status_code, 'response': r.text})

    return app

if __name__ == '__main__':
    cfg_path = os.getenv('CONFIG_PATH', 'config.yaml')
    cfg = load_config(cfg_path)
    db_path = cfg.get('db_path', 'service.db')
    init_db(db_path)
    app = create_app(cfg)
    host = cfg.get('host', '127.0.0.1')
    port = cfg.get('port', 5000)
    debug = cfg.get('debug', True)
    app.run(host=host, port=port, debug=debug)