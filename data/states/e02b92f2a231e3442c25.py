from __future__ import annotations
import os
import hashlib
import sqlite3
import yaml
import requests
from flask import Flask, request, jsonify, g
from werkzeug.utils import secure_filename

CONFIG_YAML = '''
external_api: "http://example.com/api/process"
upload_folder: "uploads"
database: "files.db"
'''
config = yaml.safe_load(CONFIG_YAML)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = config['upload_folder']
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(config['database'])
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db() -> None:
    db = get_db()
    db.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            hash TEXT,
            uploaded_at TEXT
        )
    ''')
    db.commit()

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def compute_file_hash(path: str) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def save_file(file_storage) -> str:
    filename = secure_filename(file_storage.filename)
    save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file_storage.save(save_path)
    return save_path

def record_file(filename: str, file_hash: str) -> int:
    db = get_db()
    cur = db.execute(
        'INSERT INTO files (filename, hash, uploaded_at) VALUES (?, ?, datetime(\'now\'))',
        (filename, file_hash)
    )
    db.commit()
    return cur.lastrowid

def call_external_api(file_hash: str) -> dict:
    url = config['external_api']
    payload = {'hash': file_hash}
    response = requests.post(url, json=payload, timeout=5)
    return response.json()

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    path = save_file(file)
    file_hash = compute_file_hash(path)
    file_id = record_file(file.filename, file_hash)
    api_result = call_external_api(file_hash)
    return jsonify({
        'id': file_id,
        'filename': file.filename,
        'hash': file_hash,
        'api': api_result
    })

@app.route('/files/<int:file_id>', methods=['GET'])
def get_file_info(file_id):
    db = get_db()
    cur = db.execute('SELECT * FROM files WHERE id = ?', (file_id,))
    row = cur.fetchone()
    if row is None:
        return jsonify({'error': 'Not found'}), 404
    return jsonify(dict(row))

if __name__ == '__main__':
    with app.app_context():
        init_db()
    app.run(host='127.0.0.1', port=5000)