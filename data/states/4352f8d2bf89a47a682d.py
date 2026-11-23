from __future__ import print_function
import os, sys, subprocess, sqlite3, requests, yaml, hashlib
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = 'local.db'
CONFIG_PATH = 'config.yaml'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, data BLOB, hash TEXT)''')
    conn.commit()
    conn.close()

def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)

CONFIG = load_config()
REMOTE_URL = CONFIG.get('remote_url', 'http://example.com/api/sync')

def compute_hash(data):
    return hashlib.sha256(data).hexdigest()

def save_record(record_id, data):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    h = compute_hash(data)
    c.execute('INSERT OR REPLACE INTO records (id, data, hash) VALUES (?,?,?)', (record_id, sqlite3.Binary(data), h))
    conn.commit()
    conn.close()

def get_unsynced():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, data FROM records')
    rows = c.fetchall()
    conn.close()
    return rows

def push_to_remote():
    rows = get_unsynced()
    payload = []
    for rec_id, blob in rows:
        payload.append({'id': rec_id, 'data': blob.hex()})
    if payload:
        r = requests.post(REMOTE_URL, json=payload, timeout=5)
        return r.status_code, r.text
    return 200, 'no data'

def run_user_command(user_input):
    cmd = ['echo', f'Processing {user_input}']
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout.strip()

@app.route('/sync', methods=['POST'])
def sync_endpoint():
    content = request.get_json()
    if not content or 'id' not in content or 'data' not in content:
        return jsonify({'error':'invalid payload'}), 400
    rec_id = content['id']
    data = content['data'].encode()
    save_record(rec_id, data)
    cmd_output = run_user_command(rec_id)
    status, msg = push_to_remote()
    return jsonify({'status':status, 'msg':msg, 'cmd':cmd_output})

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)