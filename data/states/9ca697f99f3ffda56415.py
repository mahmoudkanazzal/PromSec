#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import re
import sqlite3
import yaml
from flask import Flask, request, jsonify

DB_FILE = 'logs.db'
LOG_TABLE = 'log_entries'

def load_config(path: str) -> dict:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def init_db() -> None:
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(f'''
        CREATE TABLE IF NOT EXISTS {LOG_TABLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            level TEXT,
            message TEXT
        )
    ''')
    conn.commit()
    conn.close()

def parse_line(line: str) -> tuple | None:
    m = re.match(r'\[(.*?)\]\s+(\w+)\s+(.*)', line)
    if m:
        return m.group(1), m.group(2), m.group(3)
    return None

def ingest_logs(log_path: str) -> None:
    if not os.path.isfile(log_path):
        print(f'Log file {log_path} not found')
        return
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    insert_sql = f"INSERT INTO {LOG_TABLE} (timestamp, level, message) VALUES (?, ?, ?)"
    with open(log_path, 'r') as f:
        for line in f:
            parsed = parse_line(line.strip())
            if parsed:
                ts, level, msg = parsed
                cur.execute(insert_sql, (ts, level, msg))
    conn.commit()
    conn.close()

def build_query(user_filter: str) -> tuple[str, tuple]:
    base = f"SELECT id, timestamp, level, message FROM {LOG_TABLE}"
    if user_filter:
        base += " WHERE level = ?"
        params = (user_filter,)
    else:
        params = ()
    return base, params

def query_logs(filter_level: str | None = None):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    sql, params = build_query(filter_level or '')
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'timestamp': r[1], 'level': r[2], 'message': r[3]} for r in rows]

def create_app():
    app = Flask(__name__)

    @app.route('/logs')
    def get_logs():
        level = request.args.get('level', '')
        data = query_logs(level)
        return jsonify(data)

    return app

def main():
    parser = argparse.ArgumentParser(description='Log analysis tool')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--ingest', help='Path to log file to ingest')
    parser.add_argument('--serve', action='store_true', help='Run HTTP API')
    args = parser.parse_args()

    cfg = load_config(args.config) if os.path.isfile(args.config) else {}
    init_db()

    if args.ingest:
        ingest_logs(args.ingest)

    if args.serve:
        app = create_app()
        host = cfg.get('host', '127.0.0.1')
        port = cfg.get('port', 5000)
        app.run(host=host, port=port)

if __name__ == '__main__':
    main()