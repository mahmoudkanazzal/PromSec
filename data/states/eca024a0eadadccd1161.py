from __future__ import annotations
import sqlite3, threading, time, subprocess, requests, json
from flask import Flask, request, jsonify

DB_PATH = 'jobs.db'
app = Flask(__name__)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        command TEXT,
        interval INTEGER,
        api_url TEXT,
        last_run REAL
    )''')
    conn.commit()
    conn.close()

def add_job(name: str, command: str, interval: int, api_url: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO jobs (name, command, interval, api_url, last_run) VALUES (?,?,?,?,0)', 
                (name, command, interval, api_url))
    job_id = cur.lastrowid
    conn.commit()
    conn.close()
    return job_id

def get_jobs() -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, name, command, interval, api_url, last_run FROM jobs')
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'command': r[2], 'interval': r[3],
             'api_url': r[4], 'last_run': r[5]} for r in rows]

def update_last_run(job_id: int, ts: float) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE jobs SET last_run=? WHERE id=?', (ts, job_id))
    conn.commit()
    conn.close()

def run_job(job: dict) -> None:
    try:
        result = subprocess.run(job['command'], shell=True, capture_output=True, text=True)
        output = result.stdout + result.stderr
    except Exception as e:
        output = str(e)
    payload = {
        'job': job['name'],
        'output': output,
        'timestamp': time.time()
    }
    try:
        requests.post(job['api_url'], json=payload)
    except Exception:
        pass

def scheduler_loop() -> None:
    while True:
        now = time.time()
        for job in get_jobs():
            if now - job['last_run'] >= job['interval']:
                run_job(job)
                update_last_run(job['id'], now)
        time.sleep(1)

@app.route('/jobs', methods=['GET'])
def list_jobs():
    return jsonify(get_jobs())

@app.route('/jobs', methods=['POST'])
def create_job():
    data = request.get_json()
    required = {'name', 'command', 'interval', 'api_url'}
    if not data or not required.issubset(data):
        return jsonify({'error': 'Missing fields'}), 400
    job_id = add_job(data['name'], data['command'], int(data['interval']), data['api_url'])
    return jsonify({'id': job_id}), 201

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)