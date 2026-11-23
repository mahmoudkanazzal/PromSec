from __future__ import annotations
import os
import uuid
import hashlib
import sqlite3
import subprocess
import shlex
from datetime import datetime
from flask import Flask, request, jsonify, g

DATABASE = 'files.db'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(e: Exception | None = None) -> None:
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db() -> None:
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id TEXT PRIMARY KEY,
            filename TEXT,
            hash TEXT,
            uploaded_at TEXT
        )
    ''')
    db.commit()

@app.teardown_appcontext
def teardown_db(exception):
    close_db(exception)

def compute_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def save_file(file_storage) -> str:
    ext = os.path.splitext(file_storage.filename)[1]
    uid = uuid.uuid4().hex
    filename = f"{uid}{ext}"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_storage.save(path)
    return path

def record_file(file_id: str, filename: str, file_hash: str) -> None:
    db = get_db()
    db.execute(
        'INSERT INTO files (id, filename, hash, uploaded_at) VALUES (?, ?, ?, ?)',
        (file_id, filename, file_hash, datetime.utcnow().isoformat())
    )
    db.commit()

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    cmd = request.form.get('cmd', '').strip()
    saved_path = save_file(file)
    file_hash = compute_hash(saved_path)
    file_id = uuid.uuid4().hex
    record_file(file_id, os.path.basename(saved_path), file_hash)

    if cmd:
        cmd_args = shlex.split(cmd)
    else:
        cmd_args = []
    full_cmd = cmd_args + [saved_path]

    result = subprocess.run(full_cmd, capture_output=True, text=True)

    response = {
        'file_id': file_id,
        'hash': file_hash,
        'command': cmd,
        'stdout': result.stdout,
        'stderr': result.stderr,
        'returncode': result.returncode
    }
    return jsonify(response)

@app.route('/files', methods=['GET'])
def list_files():
    db = get_db()
    rows = db.execute('SELECT id, filename, hash, uploaded_at FROM files').fetchall()
    files = [dict(row) for row in rows]
    return jsonify(files)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)