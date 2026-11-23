import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

admin_password = os.getenv('LIBRARIAN_PASSWORD', 'super_secret_pass_2024')
admin_secret_key = os.getenv('ADMIN_SECRET_KEY', 'admin_secret_key_2024')
password_hash = generate_password_hash(admin_password)

def verify_admin_credentials(password: str, secret_key: str) -> bool:
    return check_password_hash(password_hash, password) and secret_key == admin_secret_key

def safe_yaml_load(data: str):
    try:
        return yaml.safe_load(data)
    except yaml.YAMLError:
        return None

def is_safe_parameter(value: str) -> bool:
    return re.fullmatch(r'^[\w\-]*$', value) is not None

@app.route('/library/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    data = safe_yaml_load(raw)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    year = data.get('year_published')
    if not all([title, author, isbn]):
        return jsonify({'error': 'Missing required fields'}), 400
    if not isinstance(year, int):
        return jsonify({'error': 'year_published must be integer'}), 400
    return jsonify({'title': title, 'author': author, 'isbn': isbn, 'year_published': year})

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'message': f'Book with ISBN {isbn} removed'})

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return jsonify({'error': 'section and location required'}), 400
    if not is_safe_parameter(section) or not is_safe_parameter(location):
        return jsonify({'error': 'Invalid characters in parameters'}), 400
    try:
        subprocess.run(['python3', 'inventory_check.py', section, location], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    except subprocess.CalledProcessError:
        return jsonify({'error': 'Inventory check failed'}), 500
    return jsonify({'status': 'Inventory check completed'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json(silent=True) or {}
    password = data.get('password')
    secret_key = data.get('secret_key')
    if not password or not secret_key:
        return jsonify({'error': 'Missing credentials'}), 400
    if verify_admin_credentials(password, secret_key):
        return jsonify({'message': 'Access granted'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global password_hash
    data = request.get_json(silent=True) or {}
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not new_password:
        return jsonify({'error': 'New password required'}), 400
    if old_password and check_password_hash(password_hash, old_password):
        password_hash = generate_password_hash(new_password)
        return jsonify({'message': 'Password updated'})
    return jsonify({'error': 'Invalid old password'}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    sample = {'isbn': isbn, 'title': 'Sample Book', 'author': 'Author Name', 'year_published': 2020}
    return jsonify(sample)

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'message': f'Book {isbn} updated', 'new_title': new_title, 'new_author': new_author})

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'isbn': '111', 'title': 'First Book', 'author': 'First Author'},
        {'isbn': '222', 'title': 'Second Book', 'author': 'Second Author'}
    ]
    if section:
        return jsonify({'section': section, 'books': books})
    return jsonify({'books': books})

@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN required'}), 400
    return jsonify({'isbn': isbn, 'available': True})

@app.route('/api/request_book', methods=['POST'])
def request_book():
    data = request.get_json(silent=True) or {}
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'ISBN and user_id required'}), 400
    return jsonify({'message': f'User {user_id} requested book {isbn}'})

@app.route('/api/return_book', methods=['POST'])
def return_book():
    data = request.get_json(silent=True) or {}
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'ISBN and user_id required'}), 400
    return jsonify({'message': f'User {user_id} returned book {isbn}'})

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    raw = request.get_data(as_text=True)
    data = safe_yaml_load(raw)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML format'}), 400
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not all([isbn, user_id, review_text, isinstance(rating, int)]):
        return jsonify({'error': 'Missing required fields'}), 400
    if not (1 <= rating <= 5):
        return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    return jsonify({'message': 'Review submitted', 'isbn': isbn, 'user_id': user_id, 'rating': rating})

@app.route('/api/submit_event', methods=['POST'])
def submit_event():
    raw = request.get_data(as_text=True)
    data = safe_yaml_load(raw)
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML format'}), 400
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_date = data.get('event_date')
    if not all([event_id, event_name, event_date]):
        return jsonify({'error': 'Missing required fields'}), 400
    return jsonify({'message': 'Event submitted', 'event_id': event_id})

if __name__ == '__main__':
    app.run(debug=False)