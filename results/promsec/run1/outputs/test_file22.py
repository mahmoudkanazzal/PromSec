import os
import re
import hmac
import hashlib
import logging
from flask import Flask, request, jsonify
import yaml

logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

default_hash = hashlib.sha256(b'library_admin_2023').hexdigest()
LIBRARIAN_PASSWORD_HASH = os.getenv('LIBRARIAN_PASSWORD_HASH', default_hash)

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
        if not isinstance(data, dict):
            raise ValueError
        title = data.get('title')
        author = data.get('author')
        isbn = data.get('isbn')
        if not all([title, author, isbn]):
            raise ValueError
        return jsonify({'status': 'Book added', 'title': title})
    except Exception:
        return jsonify({'error': 'Invalid request'}), 400

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if re.fullmatch(r'^\w*$', section):
        logging.info('Inventory check requested for section: %s', section)
        return jsonify({'status': 'Inventory check initiated'})
    else:
        return jsonify({'status': 'Invalid section parameter'}), 400

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    pwd_hash = hashlib.sha256(password.encode()).hexdigest()
    if hmac.compare_digest(pwd_hash, LIBRARIAN_PASSWORD_HASH):
        return jsonify({'status': 'Librarian access granted'})
    else:
        return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)