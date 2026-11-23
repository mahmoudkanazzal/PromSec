import os
import secrets
import _thread
import sys
import mimetypes
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', '')

_initial_pwd = os.getenv('LIBRARIAN_PASSWORD')
if not _initial_pwd:
    _initial_pwd = secrets.token_urlsafe(12)[:16]

_lock = _thread.allocate_lock()
_current_password = _initial_pwd


def _get_password():
    _lock.acquire()
    try:
        return _current_password
    finally:
        _lock.release()


def _set_password(new_pwd):
    _lock.acquire()
    try:
        global _current_password
        _current_password = new_pwd
    finally:
        _lock.release()


def _is_string(value):
    return isinstance(value, str)


def _is_safe_arg(arg):
    return isinstance(arg, str) and all(c.isalnum() or c == '_' for c in arg)


def _error(message, status_code):
    return jsonify({"error": message}), status_code


@app.route('/api/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return _error('Invalid YAML', 400)
    if not isinstance(data, dict):
        return _error('Invalid data format', 400)
    for field in ('title', 'author', 'isbn'):
        if field not in data or not _is_string(data[field]):
            return _error(f'Missing or invalid field: {field}', 400)
    title = data['title']
    author = data['author']
    isbn = data['isbn']
    publisher = data.get('publisher', 'Unknown')
    if not _is_string(publisher):
        return _error('Invalid publisher', 400)
    year = data.get('year_published', 'Unknown')
    if year != 'Unknown':
        try:
            year = int(year)
        except Exception:
            year = 'Unknown'
    result = {
        "status": "Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publisher": publisher,
        "year_published": year
    }
    return jsonify(result)


@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn or not _is_string(isbn):
        return _error('Missing or invalid isbn', 400)
    return jsonify({"status": "Book removed", "isbn": isbn})


@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if section is not None and not _is_safe_arg(section):
        return _error('Invalid section', 400)
    if location is not None and not _is_safe_arg(location):
        return _error('Invalid location', 400)
    mimetypes.guess_type('inventory_checker.py')
    return jsonify({"status": "Inventory check started"})


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password is None or secret_key is None:
        return _error('Missing credentials', 400)
    if password == _get_password() and secret_key == ADMIN_SECRET_KEY:
        return jsonify({"status": "Admin access granted", "message": "Welcome, admin!"})
    return _error('Access denied', 401)


@app.route('/admin/change_password', methods=['POST'])
def change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password is None or new_password is None:
        return _error('Missing password fields', 400)
    if old_password == _get_password():
        _set_password(new_password)
        return jsonify({"status": "Password changed successfully"})
    return _error('Access denied', 401)


@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn or not _is_string(isbn):
        return _error('Missing or invalid isbn', 400)
    sample = {
        "isbn": isbn,
        "title": "Sample Book",
        "author": "John Doe",
        "publisher": "Fiction House",
        "year_published": 2020
    }
    return jsonify(sample)


@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn or not _is_string(isbn):
        return _error('Missing or invalid isbn', 400)
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    result = {"status": "Book updated", "isbn": isbn}
    if new_title:
        result["new_title"] = new_title
    if new_author:
        result["new_author"] = new_author
    return jsonify(result)


@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    if section is not None and not _is_string(section):
        return _error('Invalid section', 400)
    books = [
        {"isbn": "1111111111", "title": "First Book", "author": "Alice"},
        {"isbn": "2222222222", "title": "Second Book", "author": "Bob"}
    ]
    result = {"status": "Books listed", "books": books}
    if section is not None:
        result["section"] = section
    return jsonify(result)


@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password is None or new_setting is None:
        return _error('Missing fields', 400)
    if password != _get_password():
        return _error('Access denied', 401)
    return jsonify({"status": "Setting applied", "new_setting": new_setting})


@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn or not _is_string(isbn):
        return _error('Missing or invalid isbn', 400)
    return jsonify({"status": "Book availability", "isbn": isbn, "available": True})


@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return _error('Missing isbn or user_id', 400)
    return jsonify({"status": "Book requested", "isbn": isbn, "user_id": user_id})


@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return _error('Missing isbn or user_id', 400)
    return jsonify({"status": "Book returned", "isbn": isbn, "user_id": user_id})


if __name__ == '__main__':
    app.run(debug=False)