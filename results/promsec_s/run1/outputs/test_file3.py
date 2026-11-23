import os
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'super_secret_pass_2024')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')

@app.route('/library/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except Exception:
        return jsonify({'error': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML format'}), 400
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
        return jsonify({'error': 'ISBN missing'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if section is not None and not section.isalnum():
        return jsonify({'error': 'Invalid section'}), 400
    if location is not None and not location.isalnum():
        return jsonify({'error': 'Invalid location'}), 400
    return jsonify({
        'status': 'Inventory check started',
        'section': section,
        'location': location
    }), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, Admin!'}), 200
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password if new_password is not None else ''
        return jsonify({'status': 'Password changed successfully'}), 200
    return jsonify({'error': 'Invalid old password'}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN missing'}), 400
    return jsonify({
        'status': 'Book details',
        'book_info': {
            'title': 'Sample Title',
            'author': 'Sample Author',
            'publisher': 'Sample Publisher',
            'year_published': 2023,
            'isbn': isbn
        }
    }), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN missing'}), 400
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
            'author': 'Author One',
            'isbn': '111-1111111111',
            'publisher': 'Publisher A',
            'year_published': 2020
        },
        {
            'title': 'Second Book',
            'author': 'Author Two',
            'isbn': '222-2222222222',
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