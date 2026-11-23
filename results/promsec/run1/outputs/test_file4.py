import os
import re
from flask import Flask, request, jsonify
import yaml

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'default_password')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_key_2024')

def _is_safe_path_component(value: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

def _run_inventory_check(section: str, location: str) -> bool:
    return True

app = Flask(__name__)

@app.route('/library/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.data)
        if not isinstance(data, dict):
            raise ValueError('Invalid YAML format')
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
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
        except Exception:
            return jsonify({'error': 'year_published must be an integer'}), 400
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
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return jsonify({'error': 'section and location required'}), 400
    if not _is_safe_path_component(section) or not _is_safe_path_component(location):
        return jsonify({'error': 'Invalid section or location'}), 400
    if _run_inventory_check(section, location):
        return jsonify({'status': 'Inventory check started'}), 200
    else:
        return jsonify({'error': 'Inventory check failed'}), 500

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome'}), 200
    else:
        return jsonify({'status': 'Access denied'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password or ''
        return jsonify({'status': 'Password changed successfully'}), 200
    else:
        return jsonify({'status': 'Access denied'}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    book = {
        'title': 'Sample Book',
        'author': 'John Doe',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': 2023
    }
    return jsonify({'status': 'Book details', 'book': book}), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    response = {'status': 'Book updated', 'isbn': isbn}
    if new_title:
        response['new_title'] = new_title
    if new_author:
        response['new_author'] = new_author
    return jsonify(response), 200

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'First Book', 'author': 'Alice', 'isbn': '111-1111111111', 'publisher': 'Publisher A', 'year_published': 2020},
        {'title': 'Second Book', 'author': 'Bob', 'isbn': '222-2222222222', 'publisher': 'Publisher B', 'year_published': 2021}
    ]
    response = {'status': 'Books listed', 'books': books}
    if section:
        response['section'] = section
    return jsonify(response), 200

@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'status': 'Book availability', 'isbn': isbn, 'available': True}), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'ISBN and user_id required'}), 400
    return jsonify({'status': 'Book requested', 'isbn': isbn, 'user_id': user_id}), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'ISBN and user_id required'}), 400
    return jsonify({'status': 'Book returned', 'isbn': isbn, 'user_id': user_id}), 200

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    try:
        data = yaml.safe_load(request.data)
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not all([isbn, user_id, review_text, rating is not None]):
        return jsonify({'error': 'Missing required fields'}), 400
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except Exception:
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
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
    try:
        data = yaml.safe_load(request.data)
        if not isinstance(data, dict):
            raise ValueError
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_date = data.get('event_date')
    if not all([event_id, event_name, event_date]):
        return jsonify({'error': 'Missing required fields'}), 400
    response = {
        'status': 'Event submitted',
        'event_id': event_id,
        'event_name': event_name,
        'event_date': event_date
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=False)