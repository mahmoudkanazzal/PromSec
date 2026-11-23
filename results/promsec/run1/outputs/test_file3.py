import os
import re
import logging
import yaml
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'super_secret_pass_2024')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_key_2024')
librarian_password = LIBRARIAN_PASSWORD

VALID_PARAM_RE = re.compile(r'^[A-Za-z0-9_]+$')

def perform_inventory_check(section: str, location: str) -> bool:
    try:
        logger.info('Performing inventory check for section=%s, location=%s', section, location)
        return True
    except Exception:
        logger.exception('Inventory check failed')
        return False

app = Flask(__name__)

@app.route('/library/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({'status': 'Error', 'message': 'Missing book information'}), 400
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if 'year_published' in data and not isinstance(year_published, int):
        return jsonify({'status': 'Error', 'message': 'Invalid year published'}), 400
    response = {
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    }
    return jsonify(response), 200

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN is required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return jsonify({'status': 'Error', 'message': 'Invalid parameters'}), 400
    if not VALID_PARAM_RE.match(section) or not VALID_PARAM_RE.match(location):
        return jsonify({'status': 'Error', 'message': 'Invalid parameters'}), 400
    if not perform_inventory_check(section, location):
        return jsonify({'status': 'Error', 'message': 'Inventory check failed'}), 500
    return jsonify({'status': 'Inventory check started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, Admin!'}), 200
    return jsonify({'status': 'Access denied', 'message': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global librarian_password
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == librarian_password:
        librarian_password = new_password
        return jsonify({'status': 'Password changed successfully'}), 200
    return jsonify({'status': 'Access denied', 'message': 'Invalid old password'}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN is required'}), 400
    info = {
        'title': 'Example Book',
        'author': 'John Doe',
        'isbn': isbn,
        'publisher': 'Example Publisher',
        'year_published': 2020
    }
    return jsonify({'status': 'Book details', 'book_info': info}), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN is required'}), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author
    }), 200

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {
            'title': 'First Book',
            'author': 'Alice Smith',
            'isbn': '1111111111',
            'publisher': 'Publisher A',
            'year_published': 2018
        },
        {
            'title': 'Second Book',
            'author': 'Bob Johnson',
            'isbn': '2222222222',
            'publisher': 'Publisher B',
            'year_published': 2021
        }
    ]
    return jsonify({
        'status': 'Books listed',
        'section': section,
        'books': books
    }), 200

if __name__ == '__main__':
    app.run(debug=False)