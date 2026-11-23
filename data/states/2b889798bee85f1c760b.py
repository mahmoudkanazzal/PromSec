from __future__ import annotations

import os
import hashlib
import sqlite3
import subprocess
import json
import shlex
from flask import Flask, request, jsonify
import yaml
import requests

app = Flask(__name__)

def load_config(yaml_str: str) -> dict:
    return yaml.safe_load(yaml_str)

def init_db(db_path: str):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS records (id INTEGER PRIMARY KEY, key TEXT, value TEXT)')
    conn.commit()
    return conn

def store_record(conn, key, value):
    cur = conn.cursor()
    cur.execute('INSERT INTO records (key, value) VALUES (?, ?)', (key, value))
    conn.commit()

def get_records(conn):
    cur = conn.cursor()
    cur.execute('SELECT key, value FROM records')
    return dict(cur.fetchall())

def run_external(command: str):
    args = shlex.split(command)
    result = subprocess.run(args, capture_output=True, text=True)
    return result.stdout.strip()

def hash_content(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()

@app.route('/load', methods=['POST'])
def load():
    payload = request.get_json(force=True)
    yaml_str = payload.get('config', '')
    config = load_config(yaml_str)

    default_db = os.path.join(app.instance_path, 'microservice.db')
    db_path = config.get('database', default_db)
    conn = init_db(db_path)

    cfg_hash = hash_content(yaml_str)
    store_record(conn, 'config_hash', cfg_hash)

    cmd = config.get('command')
    cmd_output = ''
    if cmd:
        cmd_output = run_external(cmd)
        store_record(conn, 'last_command', cmd_output)

    url = config.get('fetch_url')
    fetched = ''
    if url:
        resp = requests.get(url, timeout=5)
        fetched = resp.text[:200]
        store_record(conn, 'fetched_data', fetched)

    return jsonify({
        'status': 'ok',
        'config_hash': cfg_hash,
        'command_output': cmd_output,
        'fetched_snippet': fetched
    })

@app.route('/records', methods=['GET'])
def records():
    default_db = os.path.join(app.instance_path, 'microservice.db')
    db_path = request.args.get('db', default_db)
    conn = sqlite3.connect(db_path)
    data = get_records(conn)
    return jsonify(data)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    app.run(host='127.0.0.1', port=port)