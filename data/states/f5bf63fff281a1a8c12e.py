from __future__ import print_function
import os
import io
import hashlib
import sqlite3
import pickle
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, abort

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
DB_PATH = 'uploads.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  sha256 TEXT,
                  uploaded_at TEXT)''')
    conn.commit()
    conn.close()

def compute_sha256(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

def save_file(file_storage):
    filename = file_storage.filename
    safe_name = os.path.basename(filename)
    dest = os.path.join(UPLOAD_FOLDER, safe_name)
    file_storage.save(dest)
    return dest, safe_name

class RestrictedUnpickler(pickle.Unpickler):
    # Allow only a safe subset of built-in types
    SAFE_BUILTINS = {
        'list', 'dict', 'set', 'tuple', 'int', 'float', 'str', 'bool', 'bytes'
    }

    def find_class(self, module, name):
        if module == "builtins" and name in self.SAFE_BUILTINS:
            return getattr(__import__(module), name)
        raise pickle.UnpicklingError(f"global '{module}.{name}' is forbidden")

def process_pickle(file_path):
    with open(file_path, 'rb') as f:
        data = f.read()
    # Use restricted unpickler to avoid executing arbitrary code
    obj = RestrictedUnpickler(io.BytesIO(data)).load()
    return obj

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    path, name = save_file(file)
    sha = compute_sha256(path)
    if name.lower().endswith('.pkl'):
        try:
            obj = process_pickle(path)
        except Exception as e:
            return jsonify({'error': 'Failed to deserialize', 'msg': str(e)}), 400
    else:
        obj = None
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO files (filename, sha256, uploaded_at) VALUES (?, ?, ?)',
              (name, sha, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    resp = {'filename': name, 'sha256': sha, 'uploaded_at': datetime.utcnow().isoformat()}
    if obj is not None:
        resp['deserialized'] = repr(obj)
    return jsonify(resp), 201

@app.route('/files/<path:filename>', methods=['GET'])
def get_file(filename):
    safe_name = os.path.basename(filename)
    if not os.path.isfile(os.path.join(UPLOAD_FOLDER, safe_name)):
        abort(404)
    return send_from_directory(UPLOAD_FOLDER, safe_name)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)