from __future__ import annotations
import os
import hashlib
import sqlite3
import json
import base64
import mimetypes
import yaml
from flask import Flask, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Use a safer location inside the Flask instance folder
UPLOAD_FOLDER = os.path.join(app.instance_path, 'uploads')
DB_PATH = os.path.join(app.instance_path, 'app.db')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            sha256 TEXT,
            filetype TEXT,
            extra BLOB
        )
    ''')
    conn.commit()
    conn.close()

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'log', 'yaml', 'bin'}

def compute_md5(path: str) -> str:
    # Compute SHA-256 instead of MD5 for better security
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            h.update(chunk)
    return h.hexdigest()

def get_file_type(path: str) -> str:
    # Determine MIME type based on filename extension
    mime_type, _ = mimetypes.guess_type(path)
    return mime_type or 'application/octet-stream'

def load_extra_data(path: str):
    ext = os.path.splitext(path)[1].lower()
    if ext == '.yaml':
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    else:
        # For binary or other files, read and encode content safely
        with open(path, 'rb') as f:
            data = f.read()
        return base64.b64encode(data).decode('utf-8') if data else None

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
    sha256 = compute_md5(save_path)
    ftype = get_file_type(save_path)
    extra = load_extra_data(save_path)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    extra_blob = json.dumps(extra).encode('utf-8') if extra is not None else None
    cur.execute(
        'INSERT INTO files (filename, sha256, filetype, extra) VALUES (?,?,?,?)',
        (filename, sha256, ftype, extra_blob)
    )
    conn.commit()
    conn.close()
    return jsonify({'filename': filename, 'sha256': sha256, 'type': ftype})

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
    cur.execute('SELECT filename, sha256, filetype FROM files')
    rows = cur.fetchall()
    conn.close()
    return jsonify([{'filename': r[0], 'sha256': r[1], 'type': r[2]} for r in rows])

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)