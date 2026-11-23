from __future__ import annotations
import os
import re
import yaml
import hmac
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

SECTION_PATTERN = re.compile(r'^[a-zA-Z0-9_-]*$')

def validate_book_info(book_info):
    if not isinstance(book_info, dict):
        return False, 'Payload must be a YAML mapping'
    for field in ('title', 'author', 'isbn'):
        value = book_info.get(field)
        if not isinstance(value, str) or not value.strip():
            return False, f'Field "{field}" must be a non‑empty string'
    return True, ''

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    valid, error_msg = validate_book_info(data)
    if not valid:
        return jsonify({'error': error_msg}), 400
    return jsonify({
        'status': 'New Book added',
        'title': data['title'],
        'author': data['author'],
        'isbn': data['isbn']
    })

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not SECTION_PATTERN.fullmatch(section):
        return jsonify({'error': 'Invalid section parameter'}), 400
    try:
        subprocess.run(['python', 'run_inventory.py', section],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except Exception:
        return jsonify({'error': 'Failed to start inventory'}), 500
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({'status': 'Admin access granted'})
    return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)