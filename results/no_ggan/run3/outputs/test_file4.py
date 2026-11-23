import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'super_secret_pass_2024')
LIBRARIAN_PASSWORD_HASH = generate_password_hash(LIBRARIAN_PASSWORD)
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_key_2024')


@app.route('/library/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError as e:
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
        except (ValueError, TypeError):
            return jsonify({'error': 'year_published must be integer'}), 400
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    })


@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn})


@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    pattern = re.compile(r'^\w+$')
    if not section or not location or not pattern.match(section) or not pattern.match(location):
        return jsonify({'error': 'Invalid parameters'}), 400
    try:
        result = subprocess.run(
            ['python3', 'inventory_check.py', section, location],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'Inventory check started'})


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if not password or not secret_key:
        return jsonify({'error': 'Missing credentials'}), 400
    if check_password_hash(LIBRARIAN_PASSWORD_HASH, password) and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin!'})
    return jsonify({'status': 'Access denied'}), 401


@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if not new_password:
        return jsonify({'error': 'new_password is required'}), 400
    if not old_password or not check_password_hash(LIBRARIAN_PASSWORD_HASH, old_password):
        return jsonify({'error': 'Invalid old password'}), 401
    LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)
    return jsonify({'status': 'Password changed successfully'})


@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    info = {
        'title': 'Sample Book',
        'author': 'John Doe',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': 2020
    }
    return jsonify({'status': 'Book details', 'book': info})


@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author
    })


@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222'}
    ]
    response = {'status': 'Books listed', 'books': books}
    if section:
        response['section'] = section
    return jsonify(response)


@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    availability = True
    return jsonify({
        'status': 'Book availability',
        'isbn': isbn,
        'available': availability
    })


@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'isbn and user_id are required'}), 400
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
        return jsonify({'error': 'isbn and user_id are required'}), 400
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
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not isbn or not user_id or not review_text:
        return jsonify({'error': 'Missing required fields'}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'error': 'Invalid rating'}), 400
    return jsonify({
        'status': 'Review submitted',
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating
    })


@app.route('/api/submit_event', methods=['POST'])
def submit_event():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_date = data.get('event_date')
    if not event_id or not event_name or not event_date:
        return jsonify({'error': 'Missing required fields'}), 400
    return jsonify({
        'status': 'Event submitted',
        'event_id': event_id,
        'event_name': event_name,
        'event_date': event_date
    })


if __name__ == '__main__':
    app.run(debug=False)