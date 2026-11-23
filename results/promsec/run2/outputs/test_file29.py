import os
import re
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'library_password_2024')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY', 'admin_key_2024')

def _safe_yaml_load(yaml_string):
    return yaml.safe_load(yaml_string)

def _validate_alpha_numeric(value):
    return bool(re.fullmatch(r'[\w-]+', value))

try:
    from inventory_checker import run_check as inventory_check
except Exception:
    def inventory_check(section, location):
        return True

@app.route('/api/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = _safe_yaml_load(raw)
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if not title or not author or not isbn:
        return jsonify({'status': 'Error', 'message': 'Missing required fields'}), 400
    if year_published != 'Unknown':
        try:
            int(year_published)
        except Exception:
            return jsonify({'status': 'Error', 'message': 'Invalid year_published'}), 400
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
        return jsonify({'status': 'Error', 'message': 'ISBN missing'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn})

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return jsonify({'status': 'Error', 'message': 'Missing parameters'}), 400
    if not _validate_alpha_numeric(section) or not _validate_alpha_numeric(location):
        return jsonify({'status': 'Error', 'message': 'Invalid parameters'}), 400
    try:
        result = inventory_check(section, location)
        if not result:
            raise Exception('Check failed')
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Inventory check failed'}), 500
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, Admin!'})
    return jsonify({'status': 'Access denied', 'message': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password
        return jsonify({'status': 'Password changed successfully'})
    return jsonify({'status': 'Access denied', 'message': 'Invalid old password'}), 401

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN missing'}), 400
    book = {
        'title': 'Sample Title',
        'author': 'Sample Author',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': '2020'
    }
    return jsonify({'status': 'Book details', 'book_info': book})

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN missing'}), 400
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
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111', 'publisher': 'Pub1', 'year_published': '2001'},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222', 'publisher': 'Pub2', 'year_published': '2002'}
    ]
    return jsonify({'status': 'Books listed', 'section': section, 'books': books})

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password != LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Access denied'}), 401
    if not new_setting:
        return jsonify({'status': 'Error', 'message': 'Missing new_setting'}), 400
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN missing'}), 400
    return jsonify({'status': 'Book availability', 'isbn': isbn, 'available': True})

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'status': 'Error', 'message': 'Missing parameters'}), 400
    return jsonify({'status': 'Book requested', 'isbn': isbn, 'user_id': user_id})

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'status': 'Error', 'message': 'Missing parameters'}), 400
    return jsonify({'status': 'Book returned', 'isbn': isbn, 'user_id': user_id})

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    raw = request.get_data(as_text=True)
    try:
        data = _safe_yaml_load(raw)
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not isbn or not user_id or not review_text:
        return jsonify({'status': 'Error', 'message': 'Missing required fields'}), 400
    try:
        rating_int = int(rating)
        if rating_int < 1 or rating_int > 5:
            raise ValueError
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Invalid rating'}), 400
    return jsonify({
        'status': 'Review submitted',
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating_int
    })

if __name__ == '__main__':
    app.run(debug=False)