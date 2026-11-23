from flask import Flask, request, jsonify
import os
import yaml
import re

app = Flask(__name__)
LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if LIBRARIAN_PASSWORD is None:
    raise RuntimeError('Missing environment variable: LIBRARIAN_PASSWORD')
if ADMIN_SECRET_KEY is None:
    raise RuntimeError('Missing environment variable: ADMIN_SECRET_KEY')
_param_pattern = re.compile(r'^[\w-]+$')
def _is_valid_param(value: str) -> bool:
    return bool(_param_pattern.fullmatch(value))
def _run_inventory_check(section: str, location: str) -> bool:
    return True
@app.route('/library/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing required fields'}), 400
    if 'year_published' in data and not isinstance(year_published, int):
        return jsonify({'error': 'year_published must be integer'}), 400
    response = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published,
        'status': 'Book added'
    }
    return jsonify(response)
@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'isbn': isbn, 'status': 'Book removed'})
@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return jsonify({'error': 'Missing parameters'}), 400
    if not _is_valid_param(section) or not _is_valid_param(location):
        return jsonify({'error': 'Invalid parameters'}), 400
    try:
        result = _run_inventory_check(section, location)
    except Exception:
        return jsonify({'error': 'Inventory check failed'}), 500
    if not result:
        return jsonify({'error': 'Inventory check failed'}), 500
    return jsonify({'status': 'Inventory check started'})
@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin!'})
    return jsonify({'error': 'Access denied'}), 401
@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password
        return jsonify({'status': 'Password changed'})
    return jsonify({'error': 'Access denied'}), 401
@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    info = {
        'title': 'Sample Title',
        'author': 'Sample Author',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': '2020'
    }
    return jsonify({'info': info, 'status': 'Book details'})
@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'isbn': isbn, 'new_title': new_title, 'new_author': new_author, 'status': 'Book updated'})
@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111', 'publisher': 'Pub X', 'year_published': '2001'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222', 'publisher': 'Pub Y', 'year_published': '2002'}
    ]
    return jsonify({'books': books, 'section': section, 'status': 'Books listed'})
@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'isbn': isbn, 'available': True, 'status': 'Book availability'})
@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'Missing parameters'}), 400
    return jsonify({'isbn': isbn, 'user_id': user_id, 'status': 'Book requested'})
@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'Missing parameters'}), 400
    return jsonify({'isbn': isbn, 'user_id': user_id, 'status': 'Book returned'})
@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML'}), 400
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not isbn or not user_id or not review_text or rating is None:
        return jsonify({'error': 'Missing fields'}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'error': 'Invalid rating'}), 400
    response = {
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating,
        'status': 'Review submitted'
    }
    return jsonify(response)
@app.route('/api/submit_event', methods=['POST'])
def submit_event():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML'}), 400
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_date = data.get('event_date')
    if not event_id or not event_name or not event_date:
        return jsonify({'error': 'Missing fields'}), 400
    response = {
        'event_id': event_id,
        'event_name': event_name,
        'event_date': event_date,
        'status': 'Event submitted'
    }
    return jsonify(response)
if __name__ == '__main__':
    app.run(debug=False)