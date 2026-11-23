from __future__ import print_function
import os
import hashlib
import sqlite3
from flask import Flask, request, jsonify, abort

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DATABASE = 'files.db'
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '')

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  filename TEXT,
                  checksum TEXT,
                  uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'txt', 'csv', 'png', 'jpg', 'jpeg', 'pdf'}

def compute_checksum(filepath):
    h = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()

def add_file_record(filename, checksum):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO files (filename, checksum) VALUES (?, ?)', (filename, checksum))
    conn.commit()
    conn.close()

@app.route('/upload', methods=['POST'])
def upload_file():
    pwd = request.form.get('password')
    if pwd != ADMIN_PASSWORD:
        abort(403)
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)
    checksum = compute_checksum(save_path)
    add_file_record(file.filename, checksum)
    return jsonify({'filename': file.filename, 'checksum': checksum})

@app.route('/files', methods=['GET'])
def list_files():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT filename, checksum, uploaded_at FROM files ORDER BY uploaded_at DESC')
    rows = c.fetchall()
    conn.close()
    files = [{'filename': r[0], 'checksum': r[1], 'uploaded_at': r[2]} for r in rows]
    return jsonify(files)

if __name__ == '__main__':
    init_db()
    app.run(host='127.0.0.1', port=5000)