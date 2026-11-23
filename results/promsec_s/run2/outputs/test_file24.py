from flask import Flask, request, jsonify
import os
import re
import mimetypes
from yaml import safe_load

app = Flask(__name__)
LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML'}), 400
    title = data.get('title', '')
    author = data.get('author', '')
    isbn = data.get('isbn', '')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing or empty fields'}), 400
    return jsonify({'status': 'Book added', 'title': title, 'author': author, 'isbn': isbn})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^\w*$', section):
        return jsonify({'error': 'Invalid section'}), 400
    mimetypes.guess_type(section)
    return jsonify({'status': 'Inventory check initiated'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)