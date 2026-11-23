from __future__ import print_function
import sqlite3
import threading
import time
import datetime
import json
import requests
import yaml
import hashlib
import shutil
import pathlib
import tempfile
from flask import Flask, request, jsonify

DB_PATH = 'jobs.db'
app = Flask(__name__)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            run_at TEXT NOT NULL,
            params TEXT
        )
    ''')
    conn.commit()
    conn.close()

def add_task(name, run_at, params):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    param_blob = yaml.dump(params)
    cur.execute(
        "INSERT INTO tasks (name, run_at, params) VALUES (?, ?, ?)",
        (name, run_at.isoformat(), param_blob)
    )
    conn.commit()
    conn.close()

def fetch_due_tasks():
    now = datetime.datetime.utcnow().isoformat()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT id, name, run_at, params FROM tasks WHERE run_at <= ?",
        (now,)
    )
    rows = cur.fetchall()
    conn.close()
    tasks = []
    for row in rows:
        task = {
            'id': row[0],
            'name': row[1],
            'run_at': datetime.datetime.fromisoformat(row[2]),
            'params': yaml.safe_load(row[3]) if row[3] else {}
        }
        tasks.append(task)
    return tasks

def delete_task(task_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()

def run_task(task):
    name = task['name']
    params = task['params']
    if name == 'ping':
        url = params.get('url', '')
        try:
            resp = requests.get(url, timeout=5)
            print('Ping', url, resp.status_code)
        except Exception as e:
            print('Ping error:', e)
    elif name == 'cleanup':
        raw_path = params.get('path', tempfile.gettempdir())
        try:
            base = pathlib.Path(tempfile.gettempdir()).resolve()
            target = pathlib.Path(raw_path).resolve()
            if not str(target).startswith(str(base)):
                raise ValueError('Path not allowed')
            for child in target.iterdir():
                if child.is_dir():
                    shutil.rmtree(child)
                else:
                    child.unlink()
            print('Cleanup', str(target))
        except Exception as e:
            print('Cleanup error:', e)
    elif name == 'hash':
        data = params.get('data', '')
        h = hashlib.sha256(data.encode()).hexdigest()
        print('Hash of data:', h)
    else:
        print('Unknown task:', name)

def scheduler_loop():
    while True:
        due = fetch_due_tasks()
        for task in due:
            run_task(task)
            delete_task(task['id'])
        time.sleep(10)

@app.route('/schedule', methods=['POST'])
def schedule():
    payload = request.get_json()
    name = payload.get('name')
    run_at_str = payload.get('run_at')
    params = payload.get('params', {})
    try:
        run_at = datetime.datetime.fromisoformat(run_at_str)
    except Exception:
        return jsonify({'error': 'Invalid run_at format'}), 400
    add_task(name, run_at, params)
    return jsonify({'status': 'scheduled'}), 201

def main():
    init_db()
    t = threading.Thread(target=scheduler_loop, daemon=True)
    t.start()
    app.run(host='127.0.0.1', port=5000)

if __name__ == '__main__':
    main()