from __future__ import print_function
import os
import time
import threading
import sqlite3
import datetime
import shlex
import subprocess
from flask import Flask, request, jsonify

DB_PATH = 'jobs.db'
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            command TEXT,
            run_at TEXT,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.commit()
    conn.close()

def add_job(name, command, run_at):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO jobs (name, command, run_at) VALUES (?, ?, ?)',
                (name, command, run_at))
    conn.commit()
    conn.close()

def list_jobs():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, name, command, run_at, status FROM jobs')
    rows = cur.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'command': r[2],
             'run_at': r[3], 'status': r[4]} for r in rows]

def get_due_jobs():
    now = datetime.datetime.now().isoformat(sep=' ', timespec='seconds')
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT id, name, command FROM jobs WHERE run_at <= ? AND status = ?',
                (now, 'pending'))
    jobs = cur.fetchall()
    conn.close()
    return [{'id': j[0], 'name': j[1], 'command': j[2]} for j in jobs]

def mark_job_done(job_id, success=True):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    status = 'done' if success else 'failed'
    cur.execute('UPDATE jobs SET status = ? WHERE id = ?', (status, job_id))
    conn.commit()
    conn.close()

def run_job(job):
    print('Running job:', job['id'], job['name'])
    try:
        args = shlex.split(job['command'])
        result = subprocess.run(args, capture_output=True, text=True)
        exit_code = result.returncode
    except Exception as e:
        print('Error executing command:', e)
        exit_code = 1
    success = (exit_code == 0)
    mark_job_done(job['id'], success)

def scheduler_loop():
    while True:
        due = get_due_jobs()
        for job in due:
            run_job(job)
        time.sleep(30)

@app.route('/add_job', methods=['POST'])
def api_add_job():
    data = request.get_json()
    name = data.get('name')
    command = data.get('command')
    run_at = data.get('run_at')
    add_job(name, command, run_at)
    return jsonify({'status': 'queued'}), 201

@app.route('/jobs', methods=['GET'])
def api_list_jobs():
    return jsonify(list_jobs())

def start_server():
    app.run(host='127.0.0.1', port=5000, debug=False)

if __name__ == '__main__':
    init_db()
    threading.Thread(target=scheduler_loop, daemon=True).start()
    start_server()