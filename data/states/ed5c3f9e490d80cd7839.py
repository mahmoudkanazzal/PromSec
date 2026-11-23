from __future__ import annotations
import sqlite3
import threading
import time
import subprocess
from datetime import datetime
from flask import Flask, request, jsonify
import json

DB_PATH = 'tasks.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
                (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 name TEXT,
                 command TEXT,
                 run_at TEXT,
                 status TEXT)''')
    conn.commit()
    conn.close()

def add_task(name: str, command: str, run_at: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO tasks (name, command, run_at, status) VALUES (?,?,?,?)',
              (name, command, run_at, 'pending'))
    conn.commit()
    conn.close()

def fetch_due_tasks():
    now = datetime.utcnow().strftime('%Y-%m-%d %H:%M')
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, command FROM tasks WHERE run_at <= ? AND status = ?', (now, 'pending'))
    rows = c.fetchall()
    conn.close()
    return rows

def mark_task_done(task_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE tasks SET status = ? WHERE id = ?', ('done', task_id))
    conn.commit()
    conn.close()

def execute_task(task_id: int, command: str):
    full_cmd = f"{command}"
    subprocess.run(full_cmd, shell=True)
    mark_task_done(task_id)

def scheduler_loop():
    while True:
        due = fetch_due_tasks()
        for task_id, cmd in due:
            execute_task(task_id, cmd)
        time.sleep(30)

app = Flask(__name__)

@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.get_json()
    name = data.get('name')
    command = data.get('command')
    run_at = data.get('run_at')
    add_task(name, command, run_at)
    return jsonify({'status': 'scheduled'}), 201

@app.route('/tasks', methods=['GET'])
def list_tasks():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, command, run_at, status FROM tasks')
    rows = c.fetchall()
    conn.close()
    tasks = [{'id': r[0], 'name': r[1], 'command': r[2], 'run_at': r[3], 'status': r[4]} for r in rows]
    return jsonify(tasks)

if __name__ == '__main__':
    init_db()
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)