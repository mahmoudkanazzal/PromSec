from __future__ import print_function
import os, hashlib, sqlite3, subprocess, pickle, yaml
from flask import Flask, request, jsonify, g

app = Flask(__name__)

CONFIG_PATH = 'config.yaml'
DEFAULT_CONFIG = {'UPLOAD_FOLDER': 'uploads', 'DB_PATH': 'app.db'}

def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG

config = load_config()
os.makedirs(config['UPLOAD_FOLDER'], exist_ok=True)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(config['DB_PATH'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    db.execute('''CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        token_hash TEXT,
        file_info TEXT,
        metadata BLOB
    )''')
    db.commit()

def hash_token(token):
    return hashlib.md5(token.encode('utf-8')).hexdigest()

def process_file(path):
    result = subprocess.run(['file', path], capture_output=True, text=True)
    return result.stdout.strip()

def serialize_metadata(data):
    return pickle.dumps(data)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or 'token' not in request.form:
        return jsonify({'error': 'Missing file or token'}), 400
    file = request.files['file']
    token = request.form['token']
    filename = file.filename
    save_path = os.path.join(config['UPLOAD_FOLDER'], filename)
    file.save(save_path)

    token_hash = hash_token(token)
    file_info = process_file(save_path)
    metadata = serialize_metadata({'size': os.path.getsize(save_path)})

    db = get_db()
    db.execute('INSERT INTO uploads (filename, token_hash, file_info, metadata) VALUES (?,?,?,?)',
               (filename, token_hash, file_info, metadata))
    db.commit()

    return jsonify({'status': 'ok', 'filename': filename, 'file_info': file_info})

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)