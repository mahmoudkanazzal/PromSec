import hmac
import logging
import os
import re
import subprocess
import sys

from flask import Flask, jsonify, request
import yaml
from werkzeug.security import check_password_hash, generate_password_hash

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

LIBRARIAN_PASSWORD_HASH = os.getenv('LIBRARIAN_PASSWORD_HASH')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if not LIBRARIAN_PASSWORD_HASH or not ADMIN_SECRET_KEY:
    logger.error('Required environment variables missing')
    sys.exit(1)

ALPHANUM_DOT_DASH_PATTERN = r'^[\w.\-]+$'
ISBN_PATTERN = r'^\d{10}(\d{3})?$'
MAX_CONTENT_LENGTH = 1 * 1024 * 1024

alphanum_regex = re.compile(ALPHANUM_DOT_DASH_PATTERN)
isbn_regex = re.compile(ISBN_PATTERN)

app = Flask(__name__)

@app.before_request
def _enforce_payload_limit():
    if request.method in ('POST', 'PUT', 'PATCH'):
        if request.content_length is not None and request.content_length > MAX_CONTENT_LENGTH:
            return jsonify({'status': 'Error', 'message': 'Payload too large'}), 413

def _validate_content_length():
    if request.content_length is not None and request.content_length > MAX_CONTENT_LENGTH:
        return jsonify({'status': 'Error', 'message': 'Payload too large'}), 413
    return None

def _constant_time_compare(val1: str, val2: str) -> bool:
    return hmac.compare_digest(val1, val2)

def error_response(message, code):
    return jsonify({'status': 'Error', 'message': message}), code

@app.route('/api/add_book', methods=['POST'])
def add_book():
    resp = _validate_content_length()
    if resp:
        return resp
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return error_response('Invalid YAML payload', 400)
    if not isinstance(data, dict):
        return error_response('Payload must be a mapping', 400)
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return error_response('Missing required fields', 400)
    if not isbn_regex.match(str(isbn)):
        return error_response('Invalid ISBN format', 400)
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if year_published != 'Unknown':
        try:
            int(year_published)
        except ValueError:
            return error_response('year_published must be an integer', 400)
    book = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    }
    return jsonify({'status': 'Book added', 'book': book}), 200

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    resp = _validate_content_length()
    if resp:
        return resp
    isbn = request.form.get('isbn')
    if not isbn:
        return error_response('ISBN required', 400)
    if not isbn_regex.match(isbn):
        return error_response('Invalid ISBN format', 400)
    return jsonify({'status': 'Book removed'}), 200

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return error_response('section and location required', 400)
    if not alphanum_regex.match(section) or not alphanum_regex.match(location):
        return error_response('Invalid characters in section or location', 400)
    try:
        subprocess.run(
            ['python', 'inventory_checker.py', section, location],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
    except subprocess.CalledProcessError:
        logger.exception('Inventory checker failed')
        return error_response('Failed to start inventory check', 500)
    return jsonify({'status': 'Inventory check started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if not password or not secret_key:
        return error_response('Password and secret_key required', 400)
    if not check_password_hash(LIBRARIAN_PASSWORD_HASH, password):
        return error_response('Access denied', 401)
    if not _constant_time_compare(secret_key, ADMIN_SECRET_KEY):
        return error_response('Access denied', 401)
    return jsonify({'status': 'Admin access granted'}), 200

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not old_password or not new_password:
        return error_response('Both old_password and new_password required', 400)
    if len(new_password) < 8:
        return error_response('New password must be at least 8 characters', 400)
    if not check_password_hash(LIBRARIAN_PASSWORD_HASH, old_password):
        return error_response('Invalid old password', 401)
    LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'Password changed successfully'}), 200

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return error_response('ISBN required', 400)
    if not isbn_regex.match(isbn):
        return error_response('Invalid ISBN format', 400)
    sample = {
        'title': 'Sample Book',
        'author': 'John Doe',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': 2020
    }
    return jsonify({'status': 'Book details', 'book': sample}), 200

@app.route('/api/update_book', methods=['POST'])
def update_book():
    resp = _validate_content_length()
    if resp:
        return resp
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn or not new_title or not new_author:
        return error_response('isbn, new_title, and new_author required', 400)
    if not isbn_regex.match(isbn):
        return error_response('Invalid ISBN format', 400)
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
        {'title': 'Book One', 'author': 'Author A', 'isbn': '1234567890'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '0987654321'}
    ]
    response = {'status': 'Books listed', 'books': books}
    if section:
        response['section'] = section
    return jsonify(response), 200

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if not password or not new_setting:
        return error_response('password and new_setting required', 400)
    if not check_password_hash(LIBRARIAN_PASSWORD_HASH, password):
        return error_response('Access denied', 401)
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting}), 200

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return error_response('ISBN required', 400)
    if not isbn_regex.match(isbn):
        return error_response('Invalid ISBN format', 400)
    return jsonify({'status': 'Book availability', 'available': True}), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    resp = _validate_content_length()
    if resp:
        return resp
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return error_response('isbn and user_id required', 400)
    if not isbn_regex.match(isbn):
        return error_response('Invalid ISBN format', 400)
    return jsonify({'status': 'Book requested'}), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    resp = _validate_content_length()
    if resp:
        return resp
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return error_response('isbn and user_id required', 400)
    if not isbn_regex.match(isbn):
        return error_response('Invalid ISBN format', 400)
    return jsonify({'status': 'Book returned'}), 200

@app.errorhandler(Exception)
def handle_exception(e):
    logger.exception('Unhandled exception')
    return error_response('Internal server error', 500)

if __name__ == '__main__':
    app.run(debug=False)