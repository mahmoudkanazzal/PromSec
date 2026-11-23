import os
import re
import yaml
import importlib
from flask import Flask, request, jsonify

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_me_now')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_key_2024')
app = Flask(__name__)

@app.route('/api/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing required fields'}), 400
    if year_published != 'Unknown':
        try:
            year_published = int(year_published)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid year_published'}), 400
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    })

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn})

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    pattern = re.compile(r'^[\w-]+$')
    if not section or not location or not pattern.fullmatch(section) or not pattern.fullmatch(location):
        return jsonify({'error': 'Invalid parameters'}), 400
    try:
        module = importlib.import_module('inventory_checker')
        if not hasattr(module, 'main') or not callable(module.main):
            raise AttributeError
        module.main(section, location)
    except Exception as e:
        return jsonify({'error': 'Inventory start failed'}), 500
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password != LIBRARIAN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    LIBRARIAN_PASSWORD = new_password if new_password else ''
    return jsonify({'status': 'Password changed successfully'})

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({
        'status': 'Book details',
        'book_info': {
            'title': 'Placeholder Title',
            'author': 'Placeholder Author',
            'publisher': 'Placeholder Publisher',
            'year': 'Placeholder Year',
            'isbn': isbn
        }
    })

@app.route('/api/update_book', methods=['POST'])
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

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111', 'publisher': 'PubX', 'year_published': 2001},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222', 'publisher': 'PubY', 'year_published': 2002}
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
    if password != LIBRARIAN_PASSWORD:
        return jsonify({'error': 'Unauthorized'}), 401
    if not new_setting:
        return jsonify({'error': 'Invalid setting'}), 400
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
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
        return jsonify({'error': 'Missing parameters'}), 400
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
        return jsonify({'error': 'Missing parameters'}), 400
    return jsonify({
        'status': 'Book returned',
        'isbn': isbn,
        'user_id': user_id
    })

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid data format'}), 400
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not isbn or not user_id or not review_text:
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        rating_int = int(rating)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid rating'}), 400
    if rating_int < 1 or rating_int > 5:
        return jsonify({'error': 'Rating out of range'}), 400
    return jsonify({
        'status': 'Review submitted',
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating_int
    })

if __name__ == '__main__':
    app.run(debug=False)