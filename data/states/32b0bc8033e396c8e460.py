from __future__ import annotations
import os
import hashlib
import sqlite3
import subprocess
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename
import yaml
import pickle

app = Flask(__name__)
UPLOAD_FOLDER = '/tmp/uploads'
DB_PATH = '/tmp/app.db'

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            md5 TEXT,
            filetype TEXT,
            extra BLOB
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'log', 'yaml', 'bin'}

def compute_md5(path: str) -> str:
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def get_file_type(path: str) -> str:
    result = subprocess.run(['file', '--brief', '--mime-type', path], capture_output=True, text=True)
    return result.stdout.strip()

def load_extra_data(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.yaml':
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    else:
        with open(path, 'rb') as f:
            return pickle.load(f) if os.path.getsize(path) < 1024 else None

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'no selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'file type not allowed'}), 400
    filename = secure_filename(file.filename)
    save_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(save_path)
    md5 = compute_md5(save_path)
    ftype = get_file_type(save_path)
    extra = load_extra_data(save_path)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO files (filename, md5, filetype, extra) VALUES (?,?,?,?)',
                (filename, md5, ftype, pickle.dumps(extra) if extra is not None else None))
    conn.commit()
    conn.close()
    return jsonify({'filename': filename, 'md5': md5, 'type': ftype})

@app.route('/download/<name>', methods=['GET'])
def download_file(name):
    safe_name = secure_filename(name)
    path = os.path.join(UPLOAD_FOLDER, safe_name)
    if not os.path.exists(path):
        return jsonify({'error': 'file not found'}), 404
    return send_file(path, as_attachment=True)

@app.route('/list', methods=['GET'])
def list_files():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT filename, md5, filetype FROM files')
    rows = cur.fetchall()
    conn.close()
    return jsonify([{'filename': r[0], 'md5': r[1], 'type': r[2]} for r in rows])

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)