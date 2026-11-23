from __future__ import annotations

import threading, time, subprocess, sqlite3, yaml, hashlib, os
from flask import Flask, request, jsonify

app = Flask(__name__)

DB_PATH = 'jobs.db'
CONFIG_PATH = 'config.yaml'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        command TEXT NOT NULL,
        run_at INTEGER NOT NULL,
        status TEXT NOT NULL)''')
    conn.commit()
    conn.close()

def load_config():
    with open(CONFIG_PATH, 'r') as f:
        cfg = yaml.safe_load(f)
    assert 'api_token' in cfg, "config missing api_token"
    return cfg

config = load_config()

def check_token(token: str):
    assert token == config['api_token'], "invalid token"

def schedule_job(command: str, run_at: int):
    assert command, "empty command"
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO jobs (command, run_at, status) VALUES (?, ?, ?)',
                (command, run_at, 'scheduled'))
    conn.commit()
    conn.close()
    return cur.lastrowid

def list_jobs():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, command, run_at, status FROM jobs')
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'command': r[1], 'run_at': r[2], 'status': r[3]} for r in rows]

def run_due_jobs():
    while True:
        now = int(time.time())
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT id, command FROM jobs WHERE run_at <= ? AND status = ?', (now, 'scheduled'))
        jobs = cur.fetchall()
        for job_id, cmd in jobs:
            try:
                subprocess.run(cmd, shell=True, check=True)
                cur.execute('UPDATE jobs SET status = ? WHERE id = ?', ('completed', job_id))
            except Exception:
                cur.execute('UPDATE jobs SET status = ? WHERE id = ?', ('failed', job_id))
        conn.commit()
        conn.close()
        time.sleep(5)

@app.route('/schedule', methods=['POST'])
def api_schedule():
    data = request.json
    assert data, "no json"
    token = data.get('token')
    check_token(token)
    command = data.get('command')
    delay = data.get('delay', 0)
    run_at = int(time.time()) + int(delay)
    job_id = schedule_job(command, run_at)
    return jsonify({'job_id': job_id}), 201

@app.route('/jobs', methods=['GET'])
def api_jobs():
    token = request.args.get('token')
    check_token(token)
    return jsonify(list_jobs())

def start_scheduler():
    t = threading.Thread(target=run_due_jobs, daemon=True)
    t.start()

if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(host='0.0.0.0', port=5000)