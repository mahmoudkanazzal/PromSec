from __future__ import print_function
import sqlite3
import requests
import yaml
import hashlib
import pickle
import os
from flask import Flask, request, jsonify

CONFIG_PATH = 'sync_config.yaml'
DB_PATH = 'records.db'

app = Flask(__name__)

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS records
                 (id TEXT PRIMARY KEY, data BLOB, checksum TEXT)''')
    conn.commit()
    conn.close()

def compute_checksum(data):
    return hashlib.sha256(data).hexdigest()

def get_remote_records(api_url):
    resp = requests.get(api_url)
    return resp.json()

def push_record(api_url, record_id, data):
    payload = {'id': record_id, 'data': data}
    resp = requests.post(api_url, json=payload)
    return resp.status_code == 200

def load_local_record(conn, record_id):
    c = conn.cursor()
    c.execute('SELECT data, checksum FROM records WHERE id=?', (record_id,))
    row = c.fetchone()
    if row:
        return row[0], row[1]
    return None, None

def save_local_record(conn, record_id, data):
    checksum = compute_checksum(data)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO records (id, data, checksum) VALUES (?,?,?)',
              (record_id, data, checksum))
    conn.commit()

def sync():
    cfg = load_config()
    api_url = cfg['api_url']
    conn = sqlite3.connect(DB_PATH)
    remote = get_remote_records(api_url + '/list')
    for item in remote:
        rid = item['id']
        rdata = pickle.dumps(item['data'])
        local_data, local_checksum = load_local_record(conn, rid)
        remote_checksum = compute_checksum(rdata)
        if local_checksum != remote_checksum:
            save_local_record(conn, rid, rdata)
    c = conn.cursor()
    c.execute('SELECT id, data, checksum FROM records')
    for rid, data, checksum in c.fetchall():
        if not push_record(api_url + '/update', rid, pickle.loads(data)):
            print('Failed to push', rid)
    conn.close()

@app.route('/sync', methods=['POST'])
def trigger_sync():
    sync()
    return jsonify({'status': 'synced'})

if __name__ == '__main__':
    if not os.path.exists(CONFIG_PATH):
        default_cfg = {'api_url': 'http://example.com/api'}
        with open(CONFIG_PATH, 'w') as f:
            yaml.safe_dump(default_cfg, f)
    init_db()
    app.run(host='0.0.0.0', port=5000)