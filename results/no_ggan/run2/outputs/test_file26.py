import os
import hmac
import re
import subprocess
from typing import Optional
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

def constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)

def validate_book_info(book_info: dict) -> Optional[str]:
    required_keys = ('title', 'author', 'isbn')
    for key in required_keys:
        if key not in book_info:
            return f'Missing required field: {key}'
        value = book_info[key]
        if not isinstance(value, str):
            return f'Field {key} must be a string'
        if not value.strip():
            return f'Field {key} cannot be empty'
    return None

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    try:
        data = yaml.safe_load(request.data)
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'YAML must represent a mapping'}), 400
    error = validate_book_info(data)
    if error:
        return jsonify({'status': 'Error', 'message': error}), 400
    title = data['title'].strip()
    author = data['author'].strip()
    isbn = data['isbn'].strip()
    return jsonify({'status': 'New Book added', 'title': title, 'author': author, 'isbn': isbn})

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section')
    if section is not None:
        if not re.fullmatch(r'^[\w-]+$', section):
            return jsonify({'status': 'Error', 'message': 'Invalid section parameter'}), 400
    cmd = ['python3', 'run_inventory.py']
    if section:
        cmd.append(section)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Inventory execution failed'}), 500
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if constant_time_compare(password, ADMIN_PASSWORD):
        return jsonify({'status': 'Admin access granted'})
    else:
        return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)