import os
import re
import hmac
import yaml
import subprocess
from flask import Flask, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

LIBRARIAN_PASSWORD_HASH = os.getenv('LIBRARIAN_PASSWORD_HASH')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if LIBRARIAN_PASSWORD_HASH is None:
    raise RuntimeError('LIBRARIAN_PASSWORD_HASH not set')
if ADMIN_SECRET_KEY is None:
    raise RuntimeError('ADMIN_SECRET_KEY not set')

def verify_librarian_password(password: str) -> bool:
    return check_password_hash(LIBRARIAN_PASSWORD_HASH, password)

def update_librarian_password_hash(new_password: str):
    global LIBRARIAN_PASSWORD_HASH
    LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)

ARG_PATTERN = re.compile(r'^[\w-]{1,50}$')

def _is_valid_arg(value: str) -> bool:
    return bool(ARG_PATTERN.fullmatch(value))

MAX_YAML_SIZE = 10 * 1024

def _load_yaml_safe():
    if request.content_length is not None and request.content_length > MAX_YAML_SIZE:
        abort(413)
    try:
        data = yaml.safe_load(request.get_data())
    except yaml.YAMLError:
        abort(400)
    return data

app = Flask(__name__)

@app.route('/api/add_book', methods=['POST'])
def add_book():
    payload = _load_yaml_safe()
    if not isinstance(payload, dict):
        abort(400)
    title = payload.get('title')
    author = payload.get('author')
    isbn = payload.get('isbn')
    if not title or not author or not isbn:
        abort(400)
    publisher = payload.get('publisher', 'Unknown')
    year = payload.get('year_published', 'Unknown')
    if 'year_published' in payload and not isinstance(year, int):
        abort(400)
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year
    })

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        abort(400)
    return jsonify({
        'status': 'Book removed',
        'isbn': isbn
    })

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section', '')
    location = request.args.get('location', '')
    if not _is_valid_arg(section) or not _is_valid_arg(location):
        abort(400)
    try:
        subprocess.run(
            ['python3', 'inventory_checker.py', section, location],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        abort(500)
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password and secret_key and verify_librarian_password(password) and hmac.compare_digest(secret_key, ADMIN_SECRET_KEY):
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not new_password:
        abort(400)
    if len(new_password) < 8:
        abort(400)
    if verify_librarian_password(old_password):
        update_librarian_password_hash(new_password)
        return jsonify({'status': 'Password changed successfully'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        abort(400)
    return jsonify({
        'status': 'Book details',
        'title': 'Sample Book',
        'author': 'Author Name',
        'publisher': 'Sample Publisher',
        'year_published': 2024
    })

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        abort(400)
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    response = {'status': 'Book updated', 'isbn': isbn}
    if new_title is not None:
        response['new_title'] = new_title
    if new_author is not None:
        response['new_author'] = new_author
    return jsonify(response)

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section', '')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222'}
    ]
    return jsonify({
        'status': 'Books listed',
        'section': section,
        'books': books
    })

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if not verify_librarian_password(password):
        return jsonify({'status': 'Access denied'}), 401
    if not new_setting:
        abort(400)
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        abort(400)
    return jsonify({
        'status': 'Book availability',
        'isbn': isbn,
        'available': True
    })

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        abort(400)
    return jsonify({
        'status': 'Book requested',
        'isbn': isbn,
        'user_id': user_id
    })

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        abort(400)
    return jsonify({
        'status': 'Book returned',
        'isbn': isbn,
        'user_id': user_id
    })

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    payload = _load_yaml_safe()
    if not isinstance(payload, dict):
        abort(400)
    isbn = payload.get('isbn')
    user_id = payload.get('user_id')
    review_text = payload.get('review_text')
    if not isbn or not user_id or not review_text:
        abort(400)
    rating = payload.get('rating', 0)
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        abort(400)
    return jsonify({
        'status': 'Review submitted',
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating
    })

if __name__ == '__main__':
    app.run(debug=False)