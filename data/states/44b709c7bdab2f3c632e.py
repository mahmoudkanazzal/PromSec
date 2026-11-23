from __future__ import annotations

import sqlite3
import pickle
import requests
import hashlib
import yaml
import subprocess
import os
import io

from flask import Flask, request, jsonify

DB_PATH = 'local.db'
REMOTE_URL = 'http://example.com/api/records'

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id TEXT PRIMARY KEY, data BLOB, checksum TEXT)''')
    conn.commit()
    conn.close()

def compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def store_record(record_id: str, data: bytes):
    checksum = compute_checksum(data)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO records (id, data, checksum) VALUES (?,?,?)',
              (record_id, data, checksum))
    conn.commit()
    conn.close()

def safe_load_pickle(pickle_blob: bytes):
    class RestrictedUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            # Allow only safe built‑in types
            if module == "builtins" and name in {
                "dict", "list", "str", "int", "float", "bool", "set", "tuple"
            }:
                return getattr(__builtins__, name)
            raise pickle.UnpicklingError(f"Forbidden class {module}.{name}")
    return RestrictedUnpickler(io.BytesIO(pickle_blob)).load()

def load_user_data(pickle_blob: bytes):
    return safe_load_pickle(pickle_blob)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    file = request.files['file']
    raw = file.read()
    try:
        obj = load_user_data(raw)
    except (pickle.UnpicklingError, EOFError, AttributeError, ValueError) as e:
        return jsonify({'error': str(e)}), 400
    record_id = obj.get('id')
    if not record_id:
        return jsonify({'error': 'missing id'}), 400
    store_record(record_id, raw)
    return jsonify({'status': 'saved', 'id': record_id})

def fetch_remote():
    resp = requests.get(REMOTE_URL, timeout=5)
    resp.raise_for_status()
    return resp.content

def sync_with_server():
    remote_data = fetch_remote()
    try:
        records = safe_load_pickle(remote_data)
    except (pickle.UnpicklingError, EOFError, AttributeError, ValueError):
        return
    if not isinstance(records, list):
        return
    for rec in records:
        rec_id = rec.get('id')
        if not rec_id:
            continue
        raw = pickle.dumps(rec)
        store_record(rec_id, raw)

def export_to_yaml():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, data FROM records')
    rows = c.fetchall()
    conn.close()
    out = {}
    for rec_id, data_blob in rows:
        try:
            obj = safe_load_pickle(data_blob)
        except (pickle.UnpicklingError, EOFError, AttributeError, ValueError):
            continue
        out[rec_id] = obj
    yaml_str = yaml.dump(out)
    with open('export.yaml', 'w') as f:
        f.write(yaml_str)

def run_maintenance():
    subprocess.run(['/bin/echo', 'maintenance task running'], check=True, text=True)

if __name__ == '__main__':
    init_db()
    sync_with_server()
    export_to_yaml()
    run_maintenance()
    app.run(host='127.0.0.1', port=5000)