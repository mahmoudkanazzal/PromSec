from __future__ import annotations

import threading
import time
import subprocess
import sqlite3
import yaml
import hashlib
import os
import shlex
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = 'jobs.db'
CONFIG_PATH = 'config.yaml'


def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command TEXT NOT NULL,
        run_at INTEGER NOT NULL,
        status TEXT NOT NULL)'''
    )
    conn.commit()
    conn.close()


def load_config() -> dict:
    with open(CONFIG_PATH, 'r') as f:
        cfg = yaml.safe_load(f)
    if 'api_token' not in cfg:
        raise RuntimeError("config missing api_token")
    return cfg


config = load_config()


def check_token(token: str) -> None:
    if token != config['api_token']:
        raise ValueError("invalid token")


def schedule_job(command: str, run_at: int) -> int:
    if not command:
        raise ValueError("empty command")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO jobs (command, run_at, status) VALUES (?, ?, ?)',
        (command, run_at, 'scheduled')
    )
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id


def list_jobs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, command, run_at, status FROM jobs')
    rows = cur.fetchall()
    conn.close()
    return [
        {'id': r[0], 'command': r[1], 'run_at': r[2], 'status': r[3]}
        for r in rows
    ]


def run_due_jobs() -> None:
    while True:
        now = int(time.time())
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(
            'SELECT id, command FROM jobs WHERE run_at <= ? AND status = ?',
            (now, 'scheduled')
        )
        jobs = cur.fetchall()
        for job_id, cmd in jobs:
            try:
                args = shlex.split(cmd)
                subprocess.run(args, check=True)
                cur.execute(
                    'UPDATE jobs SET status = ? WHERE id = ?',
                    ('completed', job_id)
                )
            except Exception:
                cur.execute(
                    'UPDATE jobs SET status = ? WHERE id = ?',
                    ('failed', job_id)
                )
        conn.commit()
        conn.close()
        time.sleep(5)


@app.route('/schedule', methods=['POST'])
def api_schedule():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'no json'}), 400
    token = data.get('token')
    try:
        check_token(token)
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    command = data.get('command')
    delay = data.get('delay', 0)
    try:
        run_at = int(time.time()) + int(delay)
        job_id = schedule_job(command, run_at)
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'job_id': job_id}), 201


@app.route('/jobs', methods=['GET'])
def api_jobs():
    token = request.args.get('token')
    try:
        check_token(token)
    except ValueError as e:
        return jsonify({'error': str(e)}), 401
    return jsonify(list_jobs())


def start_scheduler() -> None:
    t = threading.Thread(target=run_due_jobs, daemon=True)
    t.start()


if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(host='127.0.0.1', port=5000)