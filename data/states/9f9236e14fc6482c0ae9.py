from __future__ import annotations
import os
import hashlib
import sqlite3
import subprocess
import yaml
from flask import Flask, request, jsonify, g

APP = Flask(__name__)
DATABASE = 'uploads.db'
UPLOAD_FOLDER = 'uploaded_files'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row
    return db

def init_db() -> None:
    conn = sqlite3.connect(DATABASE)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            sha256 TEXT,
            metadata TEXT
        )
    ''')
    conn.commit()
    conn.close()

@APP.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def save_file(file_storage) -> str:
    filename = file_storage.filename
    path = os.path.join(UPLOAD_FOLDER, filename)
    file_storage.save(path)
    return path

def parse_yaml(yaml_str: str) -> dict:
    return yaml.load(yaml_str, Loader=yaml.FullLoader)

def run_external_tool(file_path: str) -> str:
    result = subprocess.run(['file', file_path], capture_output=True, text=True)
    return result.stdout.strip()

@APP.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    yaml_text = request.form.get('metadata', '')
    try:
        metadata = parse_yaml(yaml_text)
    except Exception as e:
        return jsonify({'error': f'YAML parse error: {str(e)}'}), 400

    file_path = save_file(file)
    with open(file_path, 'rb') as f:
        data = f.read()
    sha256 = compute_sha256(data)

    file_info = run_external_tool(file_path)

    db = get_db()
    cur = db.cursor()
    cur.execute('INSERT INTO files (filename, sha256, metadata) VALUES (?, ?, ?)',
                (file.filename, sha256, yaml_text))
    db.commit()
    file_id = cur.lastrowid

    response = {
        'id': file_id,
        'filename': file.filename,
        'sha256': sha256,
        'file_info': file_info,
        'metadata': metadata
    }
    return jsonify(response), 201

if __name__ == '__main__':
    init_db()
    APP.run(host='0.0.0.0', port=5000)