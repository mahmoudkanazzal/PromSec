from __future__ import annotations
import os
import sys
import yaml
import sqlite3
import hashlib
import tempfile
import shutil
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def init_db(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            message TEXT,
            hash TEXT
        )
    ''')
    conn.commit()
    return conn

def parse_log_line(line: str) -> dict | None:
    parts = line.strip().split(' ', 2)
    if len(parts) < 3:
        return None
    ts_str, level, message = parts
    try:
        ts = datetime.strptime(ts_str, '%Y-%m-%dT%H:%M:%S')
    except ValueError:
        return None
    return {'timestamp': ts.isoformat(), 'level': level.strip('[]'), 'message': message}

def entry_matches(entry: dict, filters: dict) -> bool:
    levels = filters.get('levels')
    keywords = filters.get('keywords')
    if levels and entry['level'] not in levels:
        return False
    if keywords:
        if not any(kw in entry['message'] for kw in keywords):
            return False
    return True

def hash_message(message: str) -> str:
    return hashlib.sha256(message.encode('utf-8')).hexdigest()

def store_entry(conn: sqlite3.Connection, entry: dict) -> None:
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO logs (timestamp, level, message, hash) VALUES (?,?,?,?)',
        (entry['timestamp'], entry['level'], entry['message'], entry['hash'])
    )
    conn.commit()

def process_logs(log_path: str, config: dict, db_path: str) -> int:
    conn = init_db(db_path)
    count = 0
    with open(log_path, 'r') as f:
        for line in f:
            entry = parse_log_line(line)
            if not entry:
                continue
            if not entry_matches(entry, config.get('filters', {})):
                continue
            entry['hash'] = hash_message(entry['message'])
            store_entry(conn, entry)
            count += 1
    conn.close()
    return count

@app.route('/analyze', methods=['POST'])
def analyze_endpoint():
    if 'config' not in request.files or 'log' not in request.files:
        return jsonify({'error': 'Missing files'}), 400
    config_file = request.files['config']
    log_file = request.files['log']
    temp_dir = tempfile.mkdtemp()
    try:
        config_path = os.path.join(temp_dir, 'config.yaml')
        log_path = os.path.join(temp_dir, 'log.txt')
        db_path = os.path.join(temp_dir, 'logs.db')
        config_file.save(config_path)
        log_file.save(log_path)
        config = load_config(config_path)
        processed = process_logs(log_path, config, db_path)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    return jsonify({'processed': processed})

def main():
    if len(sys.argv) == 4:
        cfg, log, db = sys.argv[1], sys.argv[2], sys.argv[3]
        config = load_config(cfg)
        processed = process_logs(log, config, db)
        print(f'Processed {processed} entries')
    else:
        print('Usage: python script.py <config.yaml> <logfile> <database.db>')

if __name__ == '__main__':
    if len(sys.argv) > 1:
        main()
    else:
        app.run(host='127.0.0.1', port=5000)