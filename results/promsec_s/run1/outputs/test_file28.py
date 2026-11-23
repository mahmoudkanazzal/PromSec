import os
from flask import Flask, request, jsonify
from yaml import safe_load
import mimetypes

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'library_password_2024')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
librarian_password = LIBRARIAN_PASSWORD

def is_nonempty_string(value):
    return isinstance(value, str) and len(value) > 0

@app.route('/api/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
    except Exception:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not isinstance(data, dict):
        return jsonify({'error': 'Invalid YAML'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not all(isinstance(v, str) for v in (title, author, isbn)):
        return jsonify({'error': 'Missing or invalid required fields'}), 400
    publisher = data.get('publisher', 'Unknown')
    if 'publisher' in data and not isinstance(publisher, str):
        return jsonify({'error': 'Missing or invalid required fields'}), 400
    year = data.get('year_published', 'Unknown')
    if 'year_published' in data and not isinstance(year, int):
        return jsonify({'error': 'year_published must be integer'}), 400
    response = {
        'title': title,
        'author': author,
        'isbn': isbn,
        'publisher': publisher,
        'year_published': year
    }
    return jsonify(response), 200

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    return jsonify({'status': 'Book removed', 'isbn': isbn}), 200

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if section is not None:
        mimetypes.guess_type(section)
    if location is not None:
        mimetypes.guess_type(location)
    return jsonify({'status': 'Inventory check started'}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({'status': 'Admin access granted', 'message': 'Welcome, admin!'}), 200
    return jsonify({'status': 'Access denied'}), 401

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    global librarian_password
    old = request.form.get('old_password')
    new = request.form.get('new_password')
    if old == librarian_password:
        librarian_password = new if new is not None else ''
        return jsonify({'status': 'Password changed successfully'}), 200
    return jsonify({'status': 'Access denied'}), 401

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    info = {
        'isbn': isbn,
        'title': 'Sample Title',
        'author': 'Sample Author',
        'publisher': 'Sample Publisher',
        'year': 2024
    }
    return jsonify(info), 200

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    resp = {'status': 'Book updated', 'isbn': isbn}
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if new_title is not None:
        resp['new_title'] = new_title
    if new_author is not None:
        resp['new_author'] = new_author
    return jsonify(resp), 200

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {'title': 'Book One', 'author': 'Author A', 'isbn': '111', 'publisher': 'Pub1', 'year': 2020},
        {'title': 'Book Two', 'author': 'Author B', 'isbn': '222', 'publisher': 'Pub2', 'year': 2021}
    ]
    result = {'status': 'Books listed', 'books': books}
    if section is not None:
        result['section'] = section
    return jsonify(result), 200

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password != librarian_password:
        return jsonify({'status': 'Access denied'}), 401
    if not is_nonempty_string(new_setting):
        return jsonify({'status': 'Error', 'message': 'Invalid setting'}), 400
    return jsonify({'status': 'Setting applied', 'new_setting': new_setting}), 200

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({'error': 'isbn is required'}), 400
    return jsonify({'status': 'Book availability', 'isbn': isbn, 'available': True}), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'isbn and user_id are required'}), 400
    return jsonify({'status': 'Book requested', 'isbn': isbn, 'user_id': user_id}), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({'error': 'isbn and user_id are required'}), 400
    return jsonify({'status': 'Book returned', 'isbn': isbn, 'user_id': user_id}), 200

if __name__ == '__main__':
    app.run(debug=False)