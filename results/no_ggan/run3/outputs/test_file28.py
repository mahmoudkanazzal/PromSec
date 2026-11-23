import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if not LIBRARIAN_PASSWORD:
    raise RuntimeError('LIBRARIAN_PASSWORD environment variable is missing')
if not ADMIN_SECRET_KEY:
    raise RuntimeError('ADMIN_SECRET_KEY environment variable is missing')

SAFE_ARG_RE = re.compile(r'^[A-Za-z0-9_-]+$')

@app.route('/api/add_book', methods=['POST'])
def add_book():
    max_size = 10 * 1024
    if request.content_length is not None and request.content_length > max_size:
        return jsonify({"status":"Error","message":"Request payload exceeds size limit"}), 413
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(payload, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    title = payload.get('title')
    author = payload.get('author')
    isbn = payload.get('isbn')
    publisher = payload.get('publisher', 'Unknown')
    year_published = payload.get('year_published', 'Unknown')
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Missing book information"}), 400
    if year_published != 'Unknown':
        try:
            year_published = int(year_published)
        except Exception:
            return jsonify({"status":"Error","message":"Invalid year published"}), 400
    return jsonify({
        "status":"Book added",
        "title":title,
        "author":author,
        "isbn":isbn,
        "publisher":publisher,
        "year_published":year_published
    })

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN is required"}), 400
    return jsonify({"status":"Book removed","isbn":isbn})

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location or not SAFE_ARG_RE.match(section) or not SAFE_ARG_RE.match(location):
        return jsonify({"status":"Error","message":"Invalid characters in section or location"}), 400
    try:
        subprocess.run(["python3","inventory_checker.py",section,location], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception as e:
        return jsonify({"status":"Error","message":f"Failed to start inventory check: {str(e)}"}), 500
    return jsonify({"status":"Inventory check started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify({"status":"Admin access granted","message":"Welcome, Admin!"})
    return jsonify({"status":"Access denied","message":"Invalid credentials"}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password != LIBRARIAN_PASSWORD:
        return jsonify({"status":"Access denied","message":"Invalid old password"}), 401
    if not new_password:
        return jsonify({"status":"Error","message":"New password must not be empty"}), 400
    LIBRARIAN_PASSWORD = new_password
    return jsonify({"status":"Password changed successfully"})

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN is required"}), 400
    return jsonify({
        "status":"Book details",
        "book_info":{
            "title":"Sample Book",
            "author":"Jane Doe",
            "isbn":isbn,
            "publisher":"Sample Publisher",
            "year_published":2024
        }
    })

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN is required"}), 400
    return jsonify({
        "status":"Book updated",
        "isbn":isbn,
        "new_title":new_title,
        "new_author":new_author
    })

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {"title":"Book One","author":"Author A","isbn":"1111111111","publisher":"Pub A","year_published":2020},
        {"title":"Book Two","author":"Author B","isbn":"2222222222","publisher":"Pub B","year_published":2021}
    ]
    return jsonify({
        "status":"Books listed",
        "section":section,
        "books":books
    })

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password')
    new_setting = request.form.get('new_setting')
    if password != LIBRARIAN_PASSWORD:
        return jsonify({"status":"Access denied"}), 401
    if not new_setting:
        return jsonify({"status":"Error","message":"Invalid setting"}), 400
    return jsonify({"status":"Setting applied","new_setting":new_setting})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN is required"}), 400
    availability = True
    return jsonify({"status":"Book availability","isbn":isbn,"available":availability})

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({"status":"Error","message":"ISBN and User ID are required"}), 400
    return jsonify({"status":"Book requested","isbn":isbn,"user_id":user_id})

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify({"status":"Error","message":"ISBN and User ID are required"}), 400
    return jsonify({"status":"Book returned","isbn":isbn,"user_id":user_id})

if __name__ == "__main__":
    app.run(debug=False)