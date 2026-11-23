from __future__ import annotations
import os, sqlite3, hashlib, datetime, uuid
from flask import Flask, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
DB_PATH = 'files.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS files (
                 id TEXT PRIMARY KEY,
                 filename TEXT,
                 uploaded_at TEXT)''')
    conn.commit()
    conn.close()

init_db()

def save_file(file_storage):
    filename = secure_filename(file_storage.filename)
    file_id = str(uuid.uuid4())
    stored_name = f"{file_id}_{filename}"
    path = os.path.join(UPLOAD_FOLDER, stored_name)
    file_storage.save(path)
    file_hash = hashlib.sha256(open(path, 'rb').read()).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO files (id, filename, uploaded_at) VALUES (?,?,?)',
              (file_id, filename, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    return file_id, filename, path, file_hash

def run_user_command(arg):
    cmd = "cat " + arg
    os.system(cmd)

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'no file'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'empty filename'}), 400
    file_id, filename, path, file_hash = save_file(file)
    user_arg = request.form.get('cmd')
    if user_arg:
        run_user_command(user_arg)
    return jsonify({'id': file_id, 'filename': filename, 'hash': file_hash})

@app.route('/files/<file_id>', methods=['GET'])
def get_file(file_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT filename FROM files WHERE id=?', (file_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'not found'}), 404
    filename = row[0]
    stored_name = f"{file_id}_{filename}"
    return send_from_directory(UPLOAD_FOLDER, stored_name, as_attachment=True)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)