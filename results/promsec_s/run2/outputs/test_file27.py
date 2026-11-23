from __future__ import annotations
import os
import logging
import secrets
import mimetypes
from typing import Any, Dict, List
import yaml
from flask import Flask, request, jsonify, abort

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

ADMIN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if not ADMIN_PASSWORD:
    ADMIN_PASSWORD = secrets.token_urlsafe(32)
    logger.warning('LIBRARIAN_PASSWORD not set; generated temporary admin password.')

books: List[Dict[str, Any]] = []
members: List[Dict[str, Any]] = []

def find_book(isbn: str) -> Dict[str, Any] | None:
    for book in books:
        if book.get('isbn') == isbn:
            return book
    return None

def find_member(member_id: str) -> Dict[str, Any] | None:
    for member in members:
        if member.get('member_id') == member_id:
            return member
    return None

@app.errorhandler(400)
def handle_400(error):
    return jsonify(error='Bad Request', message=error.description), 400

@app.errorhandler(404)
def handle_404(error):
    return jsonify(error='Not Found', message=error.description), 404

@app.errorhandler(500)
def handle_500(error):
    return jsonify(error='Internal Server Error', message='An unexpected error occurred.'), 500

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        abort(400, description='Missing title, author, or isbn')
    if find_book(isbn):
        abort(400, description='Book with this ISBN already exists')
    books.append({'title': title, 'author': author, 'isbn': isbn})
    return jsonify(message='Book added successfully'), 201

@app.route('/execute_inventory', methods=['POST'])
def execute_inventory():
    mime_type, _ = mimetypes.guess_type('inventory.txt')
    mime_type = mime_type or 'unknown'
    return jsonify(output=f'Inventory executed, mime type: {mime_type}'), 200

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password')
    if password is None:
        abort(400, description='Password is required')
    if password != ADMIN_PASSWORD:
        abort(403, description='Invalid admin password')
    return jsonify(message='Admin access granted'), 200

@app.route('/update_book_details', methods=['PUT'])
def update_book_details():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    isbn = data.get('isbn')
    if not isbn:
        abort(400, description='ISBN is required')
    book = find_book(isbn)
    if not book:
        abort(404, description='Book not found')
    if 'title' in data:
        book['title'] = data['title']
    if 'author' in data:
        book['author'] = data['author']
    return jsonify(message='Book details updated'), 200

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    isbn = request.args.get('isbn')
    if not isbn:
        abort(400, description='ISBN query parameter is required')
    book = find_book(isbn)
    if not book:
        abort(404, description='Book not found')
    books.remove(book)
    return jsonify(message='Book deleted'), 200

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    total_books = len(books)
    total_members = len(members)
    return jsonify(total_books=total_books, total_members=total_members, books=books, members=members), 200

@app.route('/librarian_panel', methods=['GET'])
def librarian_panel():
    password = request.args.get('password')
    if password is None:
        abort(400, description='Password query parameter is required')
    if password != ADMIN_PASSWORD:
        abort(403, description='Invalid password')
    return jsonify(message='Welcome to the librarian panel'), 200

@app.route('/view_books', methods=['GET'])
def view_books():
    return jsonify(books=books), 200

@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    name = data.get('name')
    member_id = data.get('member_id')
    if not name or not member_id:
        abort(400, description='Missing name or member_id')
    if find_member(member_id):
        abort(400, description='Member with this ID already exists')
    members.append({'name': name, 'member_id': member_id})
    return jsonify(message='Member added successfully'), 201

@app.route('/update_member_details', methods=['PUT'])
def update_member_details():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    member_id = data.get('member_id')
    if not member_id:
        abort(400, description='member_id is required')
    member = find_member(member_id)
    if not member:
        abort(404, description='Member not found')
    if 'name' in data:
        member['name'] = data['name']
    return jsonify(message='Member details updated'), 200

@app.route('/load_yaml', methods=['POST'])
def load_yaml():
    if not request.is_json:
        abort(400, description='Request body must be JSON')
    data = request.get_json()
    yaml_str = data.get('yaml')
    if yaml_str is None:
        abort(400, description='YAML string is required')
    try:
        parsed = yaml.safe_load(yaml_str)
    except Exception as e:
        logger.exception('YAML parsing error')
        return jsonify(error='Invalid YAML', details=str(e)), 400
    return jsonify(parsed=parsed), 200

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)