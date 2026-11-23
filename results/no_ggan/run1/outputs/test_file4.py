import os
import hashlib
import secrets
import base64
import hmac
import re
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

_LIBRARIAN_PASSWORD_HASH = os.getenv('LIBRARIAN_PASSWORD_HASH')
_ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if _LIBRARIAN_PASSWORD_HASH is None:
    raise RuntimeError('Missing LIBRARIAN_PASSWORD_HASH environment variable')
if _ADMIN_SECRET_KEY is None:
    raise RuntimeError('Missing ADMIN_SECRET_KEY environment variable')

_PBKDF2_ITERATIONS = 200_000
_SALT_SIZE = 16
_REGEX_PATTERN = re.compile(r'^[\w-]+$')


def _hash_password_raw(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, _PBKDF2_ITERATIONS)


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(_SALT_SIZE)
    dk = _hash_password_raw(password, salt)
    return f"{base64.b64encode(salt).decode('utf-8')}${dk.hex()}"


def verify_password(provided: str, stored_hash: str) -> bool:
    try:
        salt_b64, dk_hex = stored_hash.split('$', 1)
        salt = base64.b64decode(salt_b64)
        stored_dk = bytes.fromhex(dk_hex)
        derived_dk = _hash_password_raw(provided, salt)
        return hmac.compare_digest(derived_dk, stored_dk)
    except Exception:
        return False


def safe_yaml_load(data: str):
    if len(data) > 10_000:
        raise yaml.YAMLError('Input too large')
    return yaml.safe_load(data)


@app.route('/library/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        parsed = safe_yaml_load(raw)
    except yaml.YAMLError:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(parsed, dict):
        return jsonify(error='Invalid data format'), 400
    title = parsed.get('title')
    author = parsed.get('author')
    isbn = parsed.get('isbn')
    if title is None or author is None or isbn is None:
        return jsonify(error='Missing required fields'), 400
    publisher = parsed.get('publisher', 'Unknown')
    year = parsed.get('year_published')
    if year is not None and not isinstance(year, int):
        return jsonify(error='year_published must be integer'), 400
    response = {
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year
    }
    return jsonify(response), 200


@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify(error='ISBN required'), 400
    return jsonify(status='Book removed', isbn=isbn), 200


@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return jsonify(error='Invalid parameters'), 400
    if not _REGEX_PATTERN.match(section) or not _REGEX_PATTERN.match(location):
        return jsonify(error='Invalid parameters'), 400
    try:
        subprocess.run(['python3', 'inventory_check.py', section, location],
                       stdout=subprocess.DEVNULL,
                       stderr=subprocess.DEVNULL,
                       check=True)
    except subprocess.CalledProcessError:
        return jsonify(error='Subprocess failed'), 500
    return jsonify(status='Inventory check started'), 200


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password is None or secret_key is None:
        return jsonify(status='Access denied', message='Invalid credentials'), 401
    if verify_password(password, _LIBRARIAN_PASSWORD_HASH) and hmac.compare_digest(secret_key, _ADMIN_SECRET_KEY):
        return jsonify(status='Admin access granted', message='Welcome, Admin!'), 200
    return jsonify(status='Access denied', message='Invalid credentials'), 401


@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global _LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password is None:
        return jsonify(error='old_password required'), 400
    if new_password is None:
        return jsonify(error='new_password required'), 400
    if not new_password:
        return jsonify(error='new_password cannot be empty'), 400
    if verify_password(old_password, _LIBRARIAN_PASSWORD_HASH):
        _LIBRARIAN_PASSWORD_HASH = hash_password(new_password)
        return jsonify(status='Password changed successfully'), 200
    return jsonify(status='Access denied', message='Invalid old password'), 401


@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify(error='ISBN required'), 400
    info = {
        'title': 'Sample Book',
        'author': 'John Doe',
        'publisher': 'Sample Publisher',
        'year': 2020,
        'isbn': isbn
    }
    return jsonify(status='Book details', book_info=info), 200


@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify(error='ISBN required'), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    return jsonify(status='Book updated', isbn=isbn, new_title=new_title, new_author=new_author), 200


@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222'}
    ]
    return jsonify(status='Books listed', section=section, books=books), 200


@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify(error='ISBN required'), 400
    return jsonify(status='Book availability', isbn=isbn, available=True), 200


@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify(error='ISBN and user_id required'), 400
    return jsonify(status='Book requested', isbn=isbn, user_id=user_id), 200


@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify(error='ISBN and user_id required'), 400
    return jsonify(status='Book returned', isbn=isbn, user_id=user_id), 200


@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    raw = request.get_data(as_text=True)
    try:
        parsed = safe_yaml_load(raw)
    except yaml.YAMLError:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(parsed, dict):
        return jsonify(error='Invalid data format'), 400
    isbn = parsed.get('isbn')
    user_id = parsed.get('user_id')
    review_text = parsed.get('review_text')
    rating = parsed.get('rating')
    if isbn is None or user_id is None or review_text is None:
        return jsonify(error='Missing required fields'), 400
    if rating is not None:
        if not isinstance(rating, int) or not (1 <= rating <= 5):
            return jsonify(error='Invalid rating'), 400
    response = {
        'status': 'Review submitted',
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating
    }
    return jsonify(response), 200


@app.route('/api/submit_event', methods=['POST'])
def submit_event():
    raw = request.get_data(as_text=True)
    try:
        parsed = safe_yaml_load(raw)
    except yaml.YAMLError:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(parsed, dict):
        return jsonify(error='Invalid data format'), 400
    event_id = parsed.get('event_id')
    event_name = parsed.get('event_name')
    event_date = parsed.get('event_date')
    if event_id is None or event_name is None or event_date is None:
        return jsonify(error='Missing required fields'), 400
    return jsonify(status='Event submitted', event_id=event_id, event_name=event_name, event_date=event_date), 200


if __name__ == '__main__':
    app.run(debug=False)