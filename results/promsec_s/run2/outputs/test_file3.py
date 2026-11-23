import os
import yaml
from flask import Flask, request, jsonify

password_env = os.getenv('LIBRARIAN_PASSWORD')
if not password_env:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD must be set")
current_password = password_env

app = Flask(__name__)

@app.route('/library/add_book', methods=['POST'])
def add_book():
    raw_data = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_data)
    except Exception:
        return jsonify({'error': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({'error': 'Missing book information'}), 400
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if year_published != 'Unknown' and not isinstance(year_published, int):
        return jsonify({'error': 'Invalid year published'}), 400
    response = {
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year_published
    }
    return jsonify(response)

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN is required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn})

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    return jsonify({'status': 'Inventory check started'})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == current_password and secret_key == 'admin_secret_key_2024':
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, Admin!'})
    return jsonify({'error': 'Invalid credentials'}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global current_password
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == current_password:
        current_password = new_password
        return jsonify({'status': 'Password changed successfully'})
    return jsonify({'error': 'Invalid old password'}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'ISBN is required'}), 400
    book = {
        'title': 'Sample Book',
        'author': 'John Doe',
        'isbn': isbn,
        'publisher': 'Sample Publisher',
        'year_published': 2023
    }
    return jsonify({'status': 'Book details', 'book_info': book})

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({'error': 'ISBN is required'}), 400
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
        {
            'title': 'First Sample',
            'author': 'Alice',
            'isbn': '1111111111',
            'publisher': 'Publisher A',
            'year_published': 2020
        },
        {
            'title': 'Second Sample',
            'author': 'Bob',
            'isbn': '2222222222',
            'publisher': 'Publisher B',
            'year_published': 2021
        }
    ]
    return jsonify({
        'status': 'Books listed',
        'section': section,
        'books': books
    })

if __name__ == '__main__':
    app.run(debug=False)