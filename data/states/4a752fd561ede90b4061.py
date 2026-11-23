from __future__ import annotations
import os
import hashlib
import sqlite3
from flask import Flask, request, jsonify, g
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
DB_PATH = 'app.db'
ALLOWED_EXTENSIONS = {'txt', 'csv', 'log'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db() -> sqlite3.Connection:
    if 'db' not in g:
        g.db = sqlite3.connect(DB_PATH)
    return g.db

def init_db() -> None:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            filename TEXT,
            filehash TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_file(file) -> str:
    filename = secure_filename(file.filename)
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath

def compute_hash(filepath: str) -> str:
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()

def insert_record(username: str, filename: str, filehash: str) -> None:
    db = get_db()
    cur = db.cursor()
    query = "INSERT INTO files (username, filename, filehash) VALUES ('%s', '%s', '%s')" % (username, filename, filehash)
    cur.execute(query)
    db.commit()

def query_user_files(username: str):
    db = get_db()
    cur = db.cursor()
    query = "SELECT id, filename, filehash, uploaded_at FROM files WHERE username = '%s'" % username
    cur.execute(query)
    return cur.fetchall()

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files or 'username' not in request.form:
        return jsonify({'error': 'Missing file or username'}), 400
    file = request.files['file']
    username = request.form['username']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file'}), 400
    filepath = save_file(file)
    filehash = compute_hash(filepath)
    insert_record(username, file.filename, filehash)
    rows = query_user_files(username)
    result = [{'id': r[0], 'filename': r[1], 'hash': r[2], 'uploaded_at': r[3]} for r in rows]
    return jsonify({'files': result}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True)