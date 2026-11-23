import os
import yaml
import re
import hmac
import importlib
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_me')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')

def json_error(message, status_code):
    return jsonify({'status': 'Error', 'message': message}), status_code

@app.route('/api/add_book', methods=['POST'])
def add_book():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except Exception:
        return json_error('Invalid YAML', 400)
    if not isinstance(data, dict):
        return json_error('Invalid data format', 400)
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publisher = data.get('publisher', 'Unknown')
    year = data.get('year_published', 'Unknown')
    if not isinstance(title, str) or not title.strip():
        return json_error('Title must be a non‑empty string', 400)
    if not isinstance(author, str) or not author.strip():
        return json_error('Author must be a non‑empty string', 400)
    if not isinstance(isbn, str) or not isbn.strip():
        return json_error('ISBN must be a non‑empty string', 400)
    if year != 'Unknown':
        try:
            year = int(year)
        except Exception:
            return json_error('Year must be an integer', 400)
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year
    }), 200

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return json_error('ISBN missing', 400)
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return json_error('Missing parameters', 400)
    pattern = r'[\w-]*'
    if not re.fullmatch(pattern, section) or not re.fullmatch(pattern, location):
        return json_error('Invalid parameters', 400)
    try:
        module = importlib.import_module('inventory_checker')
        if hasattr(module, 'main') and callable(module.main):
            module.main(section, location)
        elif hasattr(module, 'run_check') and callable(module.run_check):
            module.run_check(section, location)
        else:
            return json_error('No valid entry point in inventory_checker', 500)
    except Exception:
        return json_error('Failed to start inventory check', 500)
    return jsonify({'status': 'Inventory check started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    secret_key = request.form.get('secret_key', '')
    pwd_ok = hmac.compare_digest(password, LIBRARIAN_PASSWORD)
    if ADMIN_SECRET_KEY is not None:
        key_ok = hmac.compare_digest(secret_key, ADMIN_SECRET_KEY)
    else:
        key_ok = True
    if pwd_ok and key_ok:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, Admin!'}), 200
    return jsonify({'status': 'Access denied', 'message': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')
    if not hmac.compare_digest(old_password, LIBRARIAN_PASSWORD):
        return jsonify({'status': 'Access denied', 'message': 'Invalid old password'}), 401
    LIBRARIAN_PASSWORD = new_password
    return jsonify({'status': 'Password changed successfully'}), 200

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return json_error('ISBN missing', 400)
    return jsonify({
        'status': 'Book details',
        'book_info': {
            'title': 'Sample Book',
            'author': 'Jane Doe',
            'isbn': isbn,
            'publisher': 'Sample Publisher',
            'year_published': 2024
        }
    }), 200

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return json_error('ISBN missing', 400)
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author
    }), 200

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {
            'title': 'Book One',
            'author': 'Author A',
            'isbn': '1111111111',
            'publisher': 'Publisher X',
            'year_published': 2020
        },
        {
            'title': 'Book Two',
            'author': 'Author B',
            'isbn': '2222222222',
            'publisher': 'Publisher Y',
            'year_published': 2021
        }
    ]
    return jsonify({
        'status': 'Books listed',
        'section': section,
        'books': books
    }), 200

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password', '')
    new_setting = request.form.get('new_setting', '')
    if not hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({'status': 'Access denied', 'message': 'Invalid credentials'}), 401
    if not new_setting:
        return json_error('Invalid setting', 400)
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting}), 200

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return json_error('ISBN missing', 400)
    return jsonify({
        'status': 'Book availability',
        'isbn': isbn,
        'available': True
    }), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return json_error('Missing parameters', 400)
    return jsonify({
        'status': 'Book requested',
        'isbn': isbn,
        'user_id': user_id
    }), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return json_error('Missing parameters', 400)
    return jsonify({
        'status': 'Book returned',
        'isbn': isbn,
        'user_id': user_id
    }), 200

if __name__ == '__main__':
    app.run(debug=False)