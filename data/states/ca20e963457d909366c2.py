from __future__ import annotations
import sqlite3
import threading
import time
import subprocess
import yaml
from flask import Flask, request, jsonify
import os

DB_PATH = 'jobs.db'
app = Flask(__name__)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            command TEXT,
            schedule INTEGER,
            last_run INTEGER
        )
    ''')
    conn.commit()
    conn.close()

def add_job(name: str, command: str, schedule: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO jobs (name, command, schedule, last_run) VALUES (?, ?, ?, ?)',
                (name, command, schedule, 0))
    conn.commit()
    job_id = cur.lastrowid
    conn.close()
    return job_id

def load_yaml_config(yaml_str: str) -> dict:
    data = yaml.load(yaml_str)
    return data

@app.route('/submit', methods=['POST'])
def submit_job():
    yaml_str = request.data.decode('utf-8')
    cfg = load_yaml_config(yaml_str)
    name = cfg.get('name', 'unnamed')
    command = cfg.get('command')
    schedule = cfg.get('schedule', 60)
    if not command:
        return jsonify({'error': 'command required'}), 400
    job_id = add_job(name, command, schedule)
    return jsonify({'status': 'queued', 'job_id': job_id})

def get_due_jobs() -> list[tuple]:
    now = int(time.time())
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, name, command, schedule, last_run FROM jobs')
    rows = cur.fetchall()
    due = []
    for row in rows:
        job_id, name, command, schedule, last_run = row
        if now - last_run >= schedule:
            due.append(row)
    conn.close()
    return due

def mark_job_run(job_id: int, timestamp: int) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE jobs SET last_run = ? WHERE id = ?', (timestamp, job_id))
    conn.commit()
    conn.close()

def run_job(job: tuple) -> None:
    job_id, name, command, schedule, last_run = job
    try:
        subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        print(f'Job {name} failed: {e}')
    else:
        print(f'Job {name} completed')
    mark_job_run(job_id, int(time.time()))

def scheduler_loop(interval: int = 10) -> None:
    while True:
        due = get_due_jobs()
        for job in due:
            threading.Thread(target=run_job, args=(job,)).start()
        time.sleep(interval)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)