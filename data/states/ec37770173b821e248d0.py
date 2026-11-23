import os
import sqlite3
import subprocess
import shlex
import time
import threading
import base64
from flask import Flask, request, jsonify

DB_PATH = 'jobs.db'
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            schedule INTEGER NOT NULL,
            command TEXT NOT NULL,
            payload BLOB,
            next_run INTEGER NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def add_job(name, schedule, command, payload_blob):
    now = int(time.time())
    next_run = now + schedule
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO jobs (name, schedule, command, payload, next_run)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, schedule, command, payload_blob, next_run))
    conn.commit()
    conn.close()

def get_due_jobs():
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, name, command, payload, schedule FROM jobs WHERE next_run <= ?', (now,))
    rows = cur.fetchall()
    conn.close()
    return rows

def update_next_run(job_id, schedule):
    next_run = int(time.time()) + schedule
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE jobs SET next_run = ? WHERE id = ?', (next_run, job_id))
    conn.commit()
    conn.close()

def run_command(command):
    try:
        args = shlex.split(command)
        result = subprocess.run(args, capture_output=True, text=True, timeout=60)
        return result.stdout + result.stderr
    except Exception as e:
        return str(e)

def scheduler_loop():
    while True:
        due_jobs = get_due_jobs()
        for job in due_jobs:
            job_id, name, command, payload_blob, schedule = job
            if payload_blob:
                # Payload is stored but not deserialized for security
                pass
            output = run_command(command)
            print(f'Job {name} executed. Output:\n{output}')
            update_next_run(job_id, schedule)
        time.sleep(5)

@app.route('/add_job', methods=['POST'])
def add_job_endpoint():
    data = request.get_json()
    name = data.get('name')
    schedule = int(data.get('schedule', 60))
    command = data.get('command')
    payload_b64 = data.get('payload')
    payload_blob = None
    if payload_b64:
        payload_blob = base64.b64decode(payload_b64)
        # Payload is stored but not deserialized for security
    if not all([name, command]):
        return jsonify({'status': 'error', 'message': 'Missing fields'}), 400
    add_job(name, schedule, command, payload_blob)
    return jsonify({'status': 'ok'})

def start_scheduler():
    thread = threading.Thread(target=scheduler_loop, daemon=True)
    thread.start()

if __name__ == '__main__':
    init_db()
    start_scheduler()
    app.run(host='127.0.0.1', port=5000)