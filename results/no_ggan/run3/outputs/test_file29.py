import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

_password_hash = os.getenv('LIBRARIAN_PASSWORD_HASH')
if not _password_hash:
    _password_hash = generate_password_hash('library_password_2024')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_key_2024')

def _is_valid_identifier(value: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

@app.route('/api/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'YAML must be a mapping'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title:
        return jsonify({'error': 'Missing or empty title'}), 400
    if not author:
        return jsonify({'error': 'Missing or empty author'}), 400
    if not isbn:
        return jsonify({'error': 'Missing or empty isbn'}), 400
    year = data.get('year_published', 'Unknown')
    if year != 'Unknown':
        try:
            year = int(year)
        except (ValueError, TypeError):
            return jsonify({'error': 'year_published must be integer'}), 400
    response = {
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'year_published': year
    }
    return jsonify(response)

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'status': f'Book with isbn {isbn} removed'})

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not _is_valid_identifier(section):
        return jsonify({'error': 'Invalid section'}), 400
    if not location or not _is_valid_identifier(location):
        return jsonify({'error': 'Invalid location'}), 400
    try:
        subprocess.run(['python3', 'inventory_checker.py', section, location], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Failed to start inventory check'}), 500
    return jsonify({'status': 'Inventory check started', 'section': section, 'location': location})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if not password or not secret_key:
        return jsonify({'error': 'Missing credentials'}), 400
    if check_password_hash(_password_hash, password) and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted'})
    return jsonify({'error': 'Access denied'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global _password_hash
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password required'}), 400
    if not old_password or not check_password_hash(_password_hash, old_password):
        return jsonify({'error': 'Access denied'}), 401
    _password_hash = generate_password_hash(new_password)
    return jsonify({'status': 'Password changed successfully'})

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    info = {
        'title': 'Sample Book',
        'author': 'Jane Doe',
        'publisher': 'Sample Publisher',
        'year': 2024
    }
    return jsonify({'status': 'Book details', 'isbn': isbn, 'info': info})

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'status': 'Book updated', 'isbn': isbn, 'new_title': new_title, 'new_author': new_author})

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '1111111111'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '2222222222'}
    ]
    return jsonify({'status': 'Books listed', 'section': section, 'books': books})

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if not password or not check_password_hash(_password_hash, password):
        return jsonify({'error': 'Access denied'}), 401
    if not new_setting:
        return jsonify({'error': 'New setting required'}), 400
    return jsonify({'status': f'Setting applied: {new_setting}'})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'status': 'Book availability', 'isbn': isbn, 'available': True})

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'Missing isbn or user_id'}), 400
    return jsonify({'status': 'Book request submitted', 'isbn': isbn, 'user_id': user_id})

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'Missing isbn or user_id'}), 400
    return jsonify({'status': 'Book return recorded', 'isbn': isbn, 'user_id': user_id})

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'YAML must be a mapping'}), 400
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    if not user_id:
        return jsonify({'error': 'Missing user_id'}), 400
    if not review_text:
        return jsonify({'error': 'Missing review_text'}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'error': 'Rating must be integer between 1 and 5'}), 400
    return jsonify({'status': 'Review submitted', 'isbn': isbn, 'user_id': user_id, 'review_text': review_text, 'rating': rating})

if __name__ == '__main__':
    app.run(debug=False)