import os
import re
import subprocess
import yaml
import hmac
from flask import Flask, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

LIBRARIAN_PASSWORD_HASH = os.getenv('LIBRARIAN_PASSWORD_HASH')
if LIBRARIAN_PASSWORD_HASH is None:
    raise RuntimeError('Environment variable LIBRARIAN_PASSWORD_HASH must be set')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if ADMIN_SECRET_KEY is None:
    raise RuntimeError('Environment variable ADMIN_SECRET_KEY must be set')

app = Flask(__name__)

@app.route('/library/add_book', methods=['POST'])
def add_book():
    max_size = 1 * 1024 * 1024
    if request.content_length is not None and request.content_length > max_size:
        return jsonify({'error': 'Payload too large'}), 413
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'YAML must be a mapping'}), 400
    required = {'title', 'author', 'isbn'}
    if not required.issubset(data.keys()):
        return jsonify({'error': 'Missing required fields'}), 400
    year = data.get('year_published', 'Unknown')
    if 'year_published' in data:
        if not isinstance(year, int):
            return jsonify({'error': 'year_published must be integer'}), 400
    else:
        year = 'Unknown'
    publisher = data.get('publisher', 'Unknown')
    response = {
        'status': 'Book added',
        'title': data['title'],
        'author': data['author'],
        'isbn': data['isbn'],
        'year_published': year,
        'publisher': publisher
    }
    return jsonify(response), 200

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    pattern = re.compile(r'^[\w-]+$')
    if not section or not location or not pattern.fullmatch(section) or not pattern.fullmatch(location):
        return jsonify({'error': 'Invalid parameters'}), 400
    try:
        result = subprocess.run(
            ['python3', 'inventory_check.py', section, location],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False
        )
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Inventory check timed out'}), 504
    except Exception:
        return jsonify({'error': 'Subprocess execution error'}), 500
    if result.returncode != 0:
        return jsonify({'error': 'Subprocess failed'}), 500
    return jsonify({'status': 'Inventory check started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if not password or not secret_key:
        return jsonify({'status': 'Access denied', 'message': 'Invalid credentials'}), 401
    if check_password_hash(LIBRARIAN_PASSWORD_HASH, password) and hmac.compare_digest(secret_key, ADMIN_SECRET_KEY):
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, Admin!'}), 200
    return jsonify({'status': 'Access denied', 'message': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'error': 'new_password cannot be empty'}), 400
    if not old_password or not check_password_hash(LIBRARIAN_PASSWORD_HASH, old_password):
        return jsonify({'status': 'Access denied', 'message': 'Invalid old password'}), 401
    LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'Password changed successfully'}), 200

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    info = {
        'title': 'Sample Title',
        'author': 'Sample Author',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': '2020'
    }
    return jsonify({'status': 'Book details', 'book_info': info}), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    response = {
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author
    }
    return jsonify(response), 200

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {
            'title': 'Book One',
            'author': 'Author A',
            'isbn': '1111111111',
            'publisher': 'Publisher X',
            'year_published': '2001'
        },
        {
            'title': 'Book Two',
            'author': 'Author B',
            'isbn': '2222222222',
            'publisher': 'Publisher Y',
            'year_published': '2002'
        }
    ]
    response = {
        'status': 'Books listed',
        'section': section,
        'books': books
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=False)