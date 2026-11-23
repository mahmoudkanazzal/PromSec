import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'super_secret_pass_2024')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_key_2024')
LIBRARIAN_PASSWORD_HASH = generate_password_hash(LIBRARIAN_PASSWORD)

def is_safe_path_component(value: str) -> bool:
    return re.fullmatch(r'^[A-Za-z0-9._-]+$', value) is not None

@app.route('/library/add_book', methods=['POST'])
def add_book():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    title = data.get('title', '').strip()
    author = data.get('author', '').strip()
    isbn = data.get('isbn', '').strip()
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing required fields'}), 400
    if not isinstance(year_published, int):
        return jsonify({'error': 'year_published must be an integer'}), 400
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    })

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn})

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section', '')
    location = request.args.get('location', '')
    if not is_safe_path_component(section) or not is_safe_path_component(location):
        return jsonify({'error': 'Invalid parameters'}), 400
    try:
        subprocess.run(
            ['python3', 'inventory_check.py', section, location],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Inventory check failed'}), 500
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    secret_key = request.form.get('secret_key', '')
    if check_password_hash(LIBRARIAN_PASSWORD_HASH, password) and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin!'})
    return jsonify({'error': 'Access denied'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    if not new_password:
        return jsonify({'error': 'New password cannot be empty'}), 400
    if check_password_hash(LIBRARIAN_PASSWORD_HASH, old_password):
        LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)
        return jsonify({'status': 'Password changed successfully'})
    return jsonify({'error': 'Access denied'}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({
        'status': 'Book details',
        'title': 'Sample Book',
        'author': 'John Doe',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': 2023
    })

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author
    })

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {
            'title': 'First Book',
            'author': 'Alice Smith',
            'isbn': '111-1111111111',
            'publisher': 'Publisher A',
            'year_published': 2020
        },
        {
            'title': 'Second Book',
            'author': 'Bob Johnson',
            'isbn': '222-2222222222',
            'publisher': 'Publisher B',
            'year_published': 2021
        }
    ]
    return jsonify({
        'status': 'Books listed',
        'section': section,
        'books': books
    })

if __name__ == '__main__':
    app.run(debug=False)