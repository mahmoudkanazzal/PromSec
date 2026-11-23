from flask import Flask, request, jsonify
import os
import hmac
import re
from yaml import safe_load

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw_body = request.get_data(as_text=True)
    try:
        data = safe_load(raw_body)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not isinstance(title, str) or not isinstance(author, str) or not isinstance(isbn, str):
        return jsonify({'error': 'Missing or invalid fields'}), 400
    return jsonify({'status': 'Book added', 'title': title})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^[\w-]*$', section):
        return jsonify({'error': 'Invalid section parameter'}), 400
    inventory_result = f'Inventory check for section: {section}'
    return jsonify({'status': 'Inventory check initiated', 'detail': inventory_result})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)