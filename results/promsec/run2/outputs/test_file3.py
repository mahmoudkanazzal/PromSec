import os
import re
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if not LIBRARIAN_PASSWORD:
    raise RuntimeError('Environment variable LIBRARIAN_PASSWORD is required')
if not ADMIN_SECRET_KEY:
    raise RuntimeError('Environment variable ADMIN_SECRET_KEY is required')

def _run_inventory_check(section: str, location: str) -> bool:
    return True

@app.route('/library/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publisher = data.get('publisher', 'Unknown')
    year_published = data.get('year_published', 'Unknown')
    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Missing required fields"}), 400
    if year_published != 'Unknown':
        try:
            year_published = int(year_published)
        except (ValueError, TypeError):
            return jsonify({"status": "Error", "message": "year_published must be integer"}), 400
    response = {
        "status": "Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publisher": publisher,
        "year_published": year_published
    }
    return jsonify(response), 200

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN required"}), 400
    return jsonify({"status": "Book removed", "isbn": isbn}), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section', '')
    location = request.args.get('location', '')
    if not re.fullmatch(r'[\w-]*', section) or not re.fullmatch(r'[\w-]*', location):
        return jsonify({"status": "Error", "message": "Invalid parameters"}), 400
    try:
        result = _run_inventory_check(section, location)
    except Exception:
        return jsonify({"status": "Error", "message": "Failed to start inventory check"}), 500
    if not result:
        return jsonify({"status": "Error", "message": "Failed to start inventory check"}), 500
    return jsonify({"status": "Inventory check started"}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({"status": "Admin access granted", "message": "Welcome, Admin!"}), 200
    return jsonify({"status": "Access denied", "message": "Invalid credentials"}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password
        return jsonify({"status": "Password changed successfully"}), 200
    return jsonify({"status": "Access denied", "message": "Invalid old password"}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN required"}), 400
    info = {
        "title": "Sample Book",
        "author": "Sample Author",
        "isbn": isbn,
        "publisher": "Unknown",
        "year_published": "Unknown"
    }
    return jsonify({"status": "Book details", "book": info}), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN required"}), 400
    return jsonify({
        "status": "Book updated",
        "isbn": isbn,
        "new_title": new_title,
        "new_author": new_author
    }), 200

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {"title": "Book One", "author": "Author A", "isbn": "111"},
        {"title": "Book Two", "author": "Author B", "isbn": "222"}
    ]
    response = {
        "status": "Books listed",
        "books": books,
        "section": section
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=False)