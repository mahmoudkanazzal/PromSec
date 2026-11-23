from __future__ import annotations

import os
import hashlib
import sqlite3
import yaml
import mimetypes
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, 'files.db')

app = Flask(__name__)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        sha256 TEXT,
        uploaded_at TEXT
    )''')
    conn.commit()
    conn.close()

def ensure_upload_dir() -> None:
    os.makedirs(UPLOAD_DIR, exist_ok=True)

def compute_sha256(file_path: str) -> str:
    h = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def get_mime_type(file_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type or 'application/octet-stream'

def store_file_record(filename: str, sha256: str) -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        'INSERT INTO files (filename, sha256, uploaded_at) VALUES (?,?,?)',
        (filename, sha256, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'no file part'}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({'error': 'no selected file'}), 400
    ensure_upload_dir()
    filename = secure_filename(f.filename)
    save_path = os.path.join(UPLOAD_DIR, filename)
    f.save(save_path)
    sha = compute_sha256(save_path)
    mime = get_mime_type(save_path)
    store_file_record(filename, sha)
    return jsonify({'filename': filename, 'sha256': sha, 'mime': mime})

@app.route('/files', methods=['GET'])
def list_files():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT filename, sha256, uploaded_at FROM files ORDER BY uploaded_at DESC')
    rows = cur.fetchall()
    conn.close()
    files = [{'filename': r[0], 'sha256': r[1], 'uploaded_at': r[2]} for r in rows]
    return jsonify(files)

@app.route('/download/<path:filename>', methods=['GET'])
def download_file(filename):
    safe_name = secure_filename(filename)
    return send_from_directory(UPLOAD_DIR, safe_name, as_attachment=True)

def load_config() -> dict:
    cfg_path = os.path.join(BASE_DIR, 'config.yaml')
    if os.path.exists(cfg_path):
        with open(cfg_path) as f:
            return yaml.safe_load(f) or {}
    return {}

if __name__ == '__main__':
    init_db()
    cfg = load_config()
    port = cfg.get('port', 5000)
    debug_mode = cfg.get('debug', False)
    host = cfg.get('host', '127.0.0.1')
    app.run(host=host, port=port, debug=debug_mode)