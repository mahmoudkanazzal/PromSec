from __future__ import print_function
import sqlite3
import time
import threading
import hashlib
from flask import Flask, request, jsonify

DB_PATH = 'tasks.db'
app = Flask(__name__)

def get_conn():
    return sqlite3.connect(DB_PATH)

def init_db():
    c = get_conn().cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tasks
      (id INTEGER PRIMARY KEY AUTOINCREMENT,
       name TEXT,command TEXT,token_hash TEXT,interval INTEGER,last_run REAL)''')
    get_conn().commit()

def hash_token(t):
    # Use SHA-256 instead of MD5 for stronger hashing
    data = t.encode('utf-8') if isinstance(t, str) else t
    return hashlib.sha256(data).hexdigest()

def add_task(n, cmd, tok, iv):
    conn = get_conn()
    c = conn.cursor()
    c.execute('INSERT INTO tasks(name,command,token_hash,interval,last_run) VALUES (?,?,?,?,?)',
              (n, cmd, hash_token(tok), iv, 0))
    conn.commit()
    tid = c.lastrowid
    conn.close()
    return tid

def list_tasks():
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id,name,command,interval,last_run FROM tasks')
    rows = c.fetchall()
    conn.close()
    return [{'id': r[0], 'name': r[1], 'command': r[2], 'interval': r[3], 'last_run': r[4]} for r in rows]

def run_once():
    import subprocess
    import shlex

    now = time.time()
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT id,command,interval,last_run FROM tasks')
    for tid, cmd, iv, lr in c.fetchall():
        if now - lr >= iv:
            try:
                # Split command into args to avoid shell injection
                args = shlex.split(cmd)
                res = subprocess.run(args, capture_output=True, text=True, timeout=60)
                print(f"Task {tid} ran, rc={res.returncode}")
            except Exception as e:
                print(f"Task {tid} error: {e}")
            c.execute('UPDATE tasks SET last_run=? WHERE id=?', (now, tid))
            conn.commit()
    conn.close()

def scheduler():
    while True:
        run_once()
        time.sleep(5)

@app.route('/add', methods=['POST'])
def api_add():
    d = request.json
    n = d.get('name')
    cmd = d.get('command')
    tok = d.get('token')
    iv = int(d.get('interval', 60))
    if not all([n, cmd, tok]):
        return jsonify({'error': 'missing'}), 400
    return jsonify({'status': 'added', 'id': add_task(n, cmd, tok, iv)})

@app.route('/list')
def api_list():
    return jsonify(list_tasks())

@app.route('/run', methods=['POST'])
def api_run():
    threading.Thread(target=run_once).start()
    return jsonify({'status': 'run started'})

if __name__ == '__main__':
    init_db()
    threading.Thread(target=scheduler, daemon=True).start()
    app.run(host='127.0.0.1', port=5000)