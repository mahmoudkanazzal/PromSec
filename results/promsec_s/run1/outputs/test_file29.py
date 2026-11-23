import os
import yaml
import mimetypes
from flask import Flask, request, jsonify

app = Flask(__name__)
admin_password = os.getenv('LIBRARIAN_PASSWORD', 'change_me')
ADMIN_KEY = 'admin_key_2024'
current_setting = None

def error_response(message, status=400):
    return jsonify({'error': message}), status

@app.route('/api/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return error_response('Invalid YAML')
    if not isinstance(data, dict):
        return error_response('YAML must be a mapping')
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if title is None or author is None or isbn is None:
        return error_response('Missing required fields')
    if not all(isinstance(v, str) and v for v in (title, author, isbn)):
        return error_response('title, author, and isbn must be strings')
    book = {'title': title, 'author': author, 'isbn': isbn}
    publisher = data.get('publisher')
    if publisher is not None:
        if not isinstance(publisher, str):
            return error_response('publisher must be a string')
        book['publisher'] = publisher
    year = data.get('year_published')
    if year is not None:
        try:
            year_int = int(year)
        except Exception:
            return error_response('year_published must be integer')
        book['year_published'] = year_int
    return jsonify(book)

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return error_response('isbn is required')
    return jsonify({'removed_isbn': isbn})

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    def is_safe(value):
        return value.isalnum()
    if section and not is_safe(section):
        return error_response('Invalid section parameter')
    if location and not is_safe(location):
        return error_response('Invalid location parameter')
    output = f"Inventory started for section={section or 'default'}, location={location or 'default'}"
    return jsonify({'status': 'started', 'returncode': 0, 'output': output})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password != admin_password or secret_key != ADMIN_KEY:
        return error_response('Invalid credentials', 401)
    return jsonify({'login': 'success'})

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global admin_password
    old = request.form.get('old_password')
    new = request.form.get('new_password')
    if not old or not new:
        return error_response('old_password and new_password required')
    if old != admin_password:
        return error_response('Old password does not match', 401)
    admin_password = new
    return jsonify({'password_changed': True})

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return error_response('isbn is required')
    return jsonify({'title': 'Sample Book', 'author': 'Jane Doe', 'isbn': isbn})

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return error_response('isbn is required')
    updates = {'isbn': isbn}
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if new_title:
        updates['new_title'] = new_title
    if new_author:
        updates['new_author'] = new_author
    return jsonify(updates)

@app.route('/api/list_books', methods=['GET'])
def list_books():
    return jsonify({'books': [{'title': 'Book One', 'author': 'Author A', 'isbn': '111'}, {'title': 'Book Two', 'author': 'Author B', 'isbn': '222'}]})

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    global current_setting
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password != admin_password:
        return error_response('Invalid password', 401)
    if new_setting is None:
        return error_response('new_setting is required')
    current_setting = new_setting
    return jsonify({'setting_updated': True, 'new_setting': new_setting})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return error_response('isbn is required')
    return jsonify({'isbn': isbn, 'available': True})

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return error_response('isbn and user_id are required')
    return jsonify({'requested': True, 'isbn': isbn, 'user_id': user_id})

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return error_response('isbn and user_id are required')
    return jsonify({'returned': True, 'isbn': isbn, 'user_id': user_id})

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return error_response('Invalid YAML')
    if not isinstance(data, dict):
        return error_response('YAML must be a mapping')
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if isbn is None or user_id is None or review_text is None or rating is None:
        return error_response('isbn, user_id, review_text, and rating are required')
    if not all(isinstance(v, str) for v in (isbn, user_id, review_text)):
        return error_response('isbn, user_id, and review_text must be strings')
    try:
        rating_int = int(rating)
    except Exception:
        return error_response('rating must be integer')
    if not (1 <= rating_int <= 5):
        return error_response('rating must be between 1 and 5')
    return jsonify({'isbn': isbn, 'user_id': user_id, 'review_text': review_text, 'rating': rating_int})

if __name__ == '__main__':
    app.run(debug=False)