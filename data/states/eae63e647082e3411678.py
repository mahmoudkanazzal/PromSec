from __future__ import print_function
import os, sys, json, hashlib, sqlite3, argparse, yaml, requests, threading
from flask import Flask, request, jsonify

CONFIG_FILE = 'config.yaml'
DB_FILE = 'records.db'
DEFAULT_TIMEOUT = 5  # seconds for HTTP requests


def load_config(path=CONFIG_FILE):
    if not os.path.isfile(path):
        raise FileNotFoundError("Config file missing")
    with open(path) as f:
        cfg = yaml.safe_load(f)
    if not (isinstance(cfg, dict) and 'server_url' in cfg and 'api_token' in cfg):
        raise ValueError("Invalid config")
    return cfg


def init_db(db_path=DB_FILE):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS records
        (id INTEGER PRIMARY KEY, data TEXT, modified INTEGER)''')
    conn.commit()
    return conn


def compute_local_hash(conn):
    cur = conn.cursor()
    cur.execute('SELECT id, data, modified FROM records ORDER BY id')
    rows = cur.fetchall()
    m = hashlib.sha256()
    for r in rows:
        m.update(str(r).encode('utf-8'))
    return m.hexdigest()


def fetch_remote_hash(url, token):
    resp = requests.get(
        url + '/hash',
        headers={'Authorization': f'Bearer {token}'},
        timeout=DEFAULT_TIMEOUT
    )
    if resp.status_code != 200:
        raise RuntimeError("Failed to get remote hash")
    return resp.json().get('hash')


def get_modified_records(conn, since_ts):
    cur = conn.cursor()
    cur.execute('SELECT id, data, modified FROM records WHERE modified > ?', (since_ts,))
    return cur.fetchall()


def push_changes(conn, url, token):
    cur = conn.cursor()
    cur.execute('SELECT MAX(modified) FROM records')
    last_mod = cur.fetchone()[0] or 0
    changes = get_modified_records(conn, 0)
    payload = [{'id': r[0], 'data': r[1], 'modified': r[2]} for r in changes]
    resp = requests.post(
        url + '/sync',
        json=payload,
        headers={'Authorization': f'Bearer {token}'},
        timeout=DEFAULT_TIMEOUT
    )
    if resp.status_code != 200:
        raise RuntimeError("Push failed")


def pull_changes(conn, url, token):
    resp = requests.get(
        url + '/sync',
        headers={'Authorization': f'Bearer {token}'},
        timeout=DEFAULT_TIMEOUT
    )
    if resp.status_code != 200:
        raise RuntimeError("Pull failed")
    data = resp.json()
    cur = conn.cursor()
    for rec in data:
        cur.execute(
            'INSERT OR REPLACE INTO records (id, data, modified) VALUES (?,?,?)',
            (rec['id'], rec['data'], rec['modified'])
        )
    conn.commit()


def sync():
    cfg = load_config()
    conn = init_db()
    local_hash = compute_local_hash(conn)
    remote_hash = fetch_remote_hash(cfg['server_url'], cfg['api_token'])
    if local_hash != remote_hash:
        push_changes(conn, cfg['server_url'], cfg['api_token'])
        pull_changes(conn, cfg['server_url'], cfg['api_token'])
    else:
        print("Already in sync.")
    conn.close()


def run_server(host, port, db_path):
    app = Flask(__name__)
    conn = sqlite3.connect(db_path, check_same_thread=False)

    @app.route('/hash', methods=['GET'])
    def get_hash():
        cur = conn.cursor()
        cur.execute('SELECT id, data, modified FROM records ORDER BY id')
        rows = cur.fetchall()
        m = hashlib.sha256()
        for r in rows:
            m.update(str(r).encode('utf-8'))
        return jsonify({'hash': m.hexdigest()})

    @app.route('/sync', methods=['GET', 'POST'])
    def sync_endpoint():
        if request.method == 'GET':
            cur = conn.cursor()
            cur.execute('SELECT id, data, modified FROM records')
            rows = cur.fetchall()
            payload = [{'id': r[0], 'data': r[1], 'modified': r[2]} for r in rows]
            return jsonify(payload)
        else:
            incoming = request.get_json()
            cur = conn.cursor()
            for rec in incoming:
                cur.execute(
                    'INSERT OR REPLACE INTO records (id, data, modified) VALUES (?,?,?)',
                    (rec['id'], rec['data'], rec['modified'])
                )
            conn.commit()
            return jsonify({'status': 'ok'})

    threading.Thread(target=lambda: app.run(host=host, port=port)).start()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['sync', 'server'])
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args()
    if args.mode == 'sync':
        if os.geteuid() != 0:
            raise PermissionError("Root required")
        sync()
    else:
        run_server(args.host, args.port, DB_FILE)


if __name__ == '__main__':
    main()