from __future__ import annotations
import os
import uuid
import hashlib
import sqlite3
import mimetypes
from flask import Flask, request, jsonify, abort
import yaml

UPLOAD_FOLDER = 'uploads'
DB_PATH = 'files.db'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        '''CREATE TABLE IF NOT EXISTS files
           (id TEXT PRIMARY KEY, filename TEXT, hash TEXT, mimetype TEXT)'''
    )
    conn.commit()
    conn.close()

def ensure_upload_dir() -> None:
    if not os.path.isdir(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

def compute_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def store_file_record(file_id: str, filename: str, file_hash: str, mimetype: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO files VALUES (?,?,?,?)',
              (file_id, filename, file_hash, mimetype))
    conn.commit()
    conn.close()

def process_file(filepath: str) -> str:
    mimetype, _ = mimetypes.guess_type(filepath)
    if not mimetype:
        mimetype = 'application/octet-stream'
    if mimetype == 'text/x-yaml' or filepath.lower().endswith('.yaml'):
        with open(filepath) as f:
            data = yaml.safe_load(f)
        return f'YAML with {len(data) if isinstance(data, dict) else "unknown"} keys'
    return f'Mimetype: {mimetype}'

@app.route('/upload', methods=['POST'])
def upload():
    token = request.form.get('token')
    expected_token = os.getenv('UPLOAD_TOKEN')
    if not expected_token or token != expected_token:
        abort(403, description='Invalid token')
    uploaded = request.files.get('file')
    if not uploaded:
        abort(400, description='No file part')
    if not uploaded.filename:
        abort(400, description='Empty filename')
    file_id = str(uuid.uuid4())
    safe_name = f'{file_id}_{uploaded.filename}'
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    uploaded.save(save_path)
    file_hash = compute_hash(save_path)
    info = process_file(save_path)
    store_file_record(file_id, uploaded.filename, file_hash, info)
    return jsonify({'id': file_id, 'hash': file_hash, 'info': info})

@app.route('/files', methods=['GET'])
def list_files():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, filename, hash, mimetype FROM files')
    rows = c.fetchall()
    conn.close()
    result = [
        {'id': r[0], 'filename': r[1], 'hash': r[2], 'info': r[3]}
        for r in rows
    ]
    return jsonify(result)

if __name__ == '__main__':
    ensure_upload_dir()
    init_db()
    app.run(host='127.0.0.1', port=5000)