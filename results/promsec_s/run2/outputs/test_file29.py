import os
import yaml
import importlib
from flask import Flask, request, jsonify

app = Flask(__name__)

librarian_password = os.getenv('LIBRARIAN_PASSWORD', 'change_me_securely')

try:
    inventory_module = importlib.import_module('inventory_checker')
except ImportError:
    inventory_module = None

check_inventory = getattr(inventory_module, 'check_inventory', None) if inventory_module else None
if not callable(check_inventory):
    check_inventory = None


def yaml_parse():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
        if not isinstance(data, dict):
            raise ValueError('YAML content must be a mapping')
        return data, None
    except yaml.YAMLError:
        return None, ('Invalid YAML format', 400)
    except ValueError as e:
        return None, (str(e), 400)


@app.route('/api/add_book', methods=['POST'])
def add_book():
    data, err = yaml_parse()
    if err:
        return jsonify({'error': err[0]}), err[1]
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not isinstance(title, str) or not title.strip():
        return jsonify({'error': 'Invalid or missing title'}), 400
    if not isinstance(author, str) or not author.strip():
        return jsonify({'error': 'Invalid or missing author'}), 400
    if not isinstance(isbn, str) or not isbn.strip():
        return jsonify({'error': 'Invalid or missing isbn'}), 400
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if year_published != 'Unknown':
        if not isinstance(year_published, int):
            return jsonify({'error': 'year_published must be integer'}), 400
    response = {
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    }
    return jsonify(response), 200


@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200


@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section', '')
    location = request.args.get('location', '')
    if check_inventory:
        try:
            check_inventory(section, location)
        except Exception:
            return jsonify({'error': 'Inventory check failed'}), 500
        return jsonify({'status': 'Inventory check started'}), 200
    else:
        return jsonify({'error': 'Inventory functionality not available'}), 503


@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == librarian_password and secret_key == 'admin_key_2024':
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin!'}), 200
    else:
        return jsonify({'error': 'Invalid credentials'}), 401


@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global librarian_password
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password != librarian_password:
        return jsonify({'error': 'Invalid old password'}), 401
    librarian_password = new_password or ''
    return jsonify({'status': 'Password changed successfully'}), 200


@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    info = {
        'title': 'Sample Title',
        'author': 'Sample Author',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': 2024
    }
    return jsonify({'status': 'Book details', 'book_info': info}), 200


@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author
    }), 200


@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section', '')
    books = [
        {'title': 'Sample Book 1', 'author': 'Author A', 'isbn': '1111111111'},
        {'title': 'Sample Book 2', 'author': 'Author B', 'isbn': '2222222222'}
    ]
    return jsonify({
        'status': 'Books listed',
        'section': section,
        'books': books
    }), 200


@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password != librarian_password:
        return jsonify({'error': 'Invalid credentials'}), 401
    if not new_setting:
        return jsonify({'error': 'new_setting cannot be empty'}), 400
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting}), 200


@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'Missing isbn'}), 400
    return jsonify({'status': 'Book availability', 'isbn': isbn, 'available': True}), 200


@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'Missing isbn or user_id'}), 400
    return jsonify({'status': 'Book requested', 'isbn': isbn, 'user_id': user_id}), 200


@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'Missing isbn or user_id'}), 400
    return jsonify({'status': 'Book returned', 'isbn': isbn, 'user_id': user_id}), 200


@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    data, err = yaml_parse()
    if err:
        return jsonify({'error': err[0]}), err[1]
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    rating = data.get('rating')
    if not isinstance(isbn, str) or not isbn.strip():
        return jsonify({'error': 'Invalid or missing isbn'}), 400
    if not isinstance(user_id, str) or not user_id.strip():
        return jsonify({'error': 'Invalid or missing user_id'}), 400
    if not isinstance(review_text, str) or not review_text.strip():
        return jsonify({'error': 'Invalid or missing review_text'}), 400
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        return jsonify({'error': 'Rating must be integer between 1 and 5'}), 400
    return jsonify({
        'status': 'Review submitted',
        'isbn': isbn,
        'user_id': user_id,
        'review_text': review_text,
        'rating': rating
    }), 200


if __name__ == '__main__':
    app.run(debug=False)