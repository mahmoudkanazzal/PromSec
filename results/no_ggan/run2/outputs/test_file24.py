from flask import Flask, request, jsonify
import os
import yaml
import subprocess
import re
from werkzeug.security import check_password_hash

app = Flask(__name__)

def get_librarian_hash():
    return os.getenv('LIBRARIAN_PASSWORD_HASH')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid book information'}), 400
    title = data.get('title', '')
    author = data.get('author', '')
    isbn = data.get('isbn', '')
    title = title.strip() if isinstance(title, str) else ''
    author = author.strip() if isinstance(author, str) else ''
    isbn = isbn.strip() if isinstance(isbn, str) else ''
    if not title or not author or not isbn:
        return jsonify({'error': 'Invalid book information'}), 400
    return jsonify({'status': 'Book added', 'title': title, 'author': author, 'isbn': isbn})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    section = section.strip()
    if section:
        if not re.fullmatch(r'^[\w-]+$', section):
            return jsonify({'error': 'Invalid section parameter'}), 400
    cmd = ['python', 'inventory_script.py']
    if section:
        cmd.append(section)
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        return jsonify({'error': 'Failed to start inventory check'}), 500
    return jsonify({'status': 'Inventory check initiated'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password_hash = get_librarian_hash()
    if not password_hash:
        return jsonify({'error': 'Server configuration error'}), 500
    password = request.form.get('password', '')
    if check_password_hash(password_hash, password):
        return jsonify({'status': 'Librarian access granted'})
    else:
        return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)