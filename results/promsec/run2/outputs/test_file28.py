from flask import Flask, request, jsonify
import os
import yaml
import re

app = Flask(__name__)
LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_me')

def _run_inventory_check(section: str, location: str) -> None:
    """Stub for inventory check."""
    pass

@app.route('/api/add_book', methods=['POST'])
def add_book():
    raw = request.get_data()
    try:
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    title = str(data.get('title','')).strip()
    author = str(data.get('author','')).strip()
    isbn = str(data.get('isbn','')).strip()
    publisher = str(data.get('publisher','Unknown')).strip() or 'Unknown'
    year = str(data.get('year','Unknown')).strip() or 'Unknown'
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Missing required fields"}), 400
    if year != 'Unknown':
        try:
            year_int = int(year)
            year = year_int
        except Exception:
            return jsonify({"status":"Error","message":"year_published must be integer"}), 400
    return jsonify({
        "status":"Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publisher": publisher,
        "year_published": year
    }), 200

@app.route('/api/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn','').strip()
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN required"}), 400
    return jsonify({"status":"Book removed","isbn": isbn}), 200

@app.route('/api/start_inventory', methods=['GET'])
def start_inventory():
    section = request.args.get('section','').strip()
    location = request.args.get('location','').strip()
    pattern = r'^[\w-]+$'
    if not (re.fullmatch(pattern, section) and re.fullmatch(pattern, location)):
        return jsonify({"status":"Error","message":"Invalid parameters"}), 400
    _run_inventory_check(section, location)
    return jsonify({"status":"Inventory check started"}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password','')
    secret_key = request.form.get('secret_key','')
    expected_secret = os.getenv('ADMIN_SECRET_KEY', 'admin_key_2024')
    if password == LIBRARIAN_PASSWORD and secret_key == expected_secret:
        return jsonify({"status":"Admin access granted","message":"Welcome, Admin!"}), 200
    return jsonify({"status":"Access denied","message":"Invalid credentials"}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password','')
    new_password = request.form.get('new_password','')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password
        return jsonify({"status":"Password changed successfully"}), 200
    return jsonify({"status":"Access denied","message":"Invalid old password"}), 401

@app.route('/api/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn','').strip()
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN required"}), 400
    return jsonify({
        "status":"Book details",
        "book_info":{
            "title":"Sample Title",
            "author":"Sample Author",
            "isbn": isbn,
            "publisher":"Sample Publisher",
            "year_published":"2020"
        }
    }), 200

@app.route('/api/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn','').strip()
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN required"}), 400
    return jsonify({
        "status":"Book updated",
        "isbn": isbn,
        "new_title": new_title,
        "new_author": new_author
    }), 200

@app.route('/api/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [
        {"title":"Book One","author":"Author A","isbn":"111","publisher":"Pub1","year_published":"2001"},
        {"title":"Book Two","author":"Author B","isbn":"222","publisher":"Pub2","year_published":"2002"}
    ]
    return jsonify({
        "status":"Books listed",
        "section": section,
        "books": books
    }), 200

@app.route('/admin/adjust_settings', methods=['POST'])
def adjust_settings():
    password = request.form.get('password','')
    new_setting = request.form.get('new_setting','')
    if password != LIBRARIAN_PASSWORD:
        return jsonify({"status":"Access denied"}), 401
    if not new_setting:
        return jsonify({"status":"Error","message":"New setting required"}), 400
    return jsonify({"status":"Setting applied","new_setting": new_setting}), 200

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn','').strip()
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN required"}), 400
    return jsonify({"status":"Book availability","isbn": isbn,"available": True}), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn','').strip()
    user_id = request.form.get('user_id','').strip()
    if not isbn or not user_id:
        return jsonify({"status":"Error","message":"ISBN and user_id required"}), 400
    return jsonify({"status":"Book requested","isbn": isbn,"user_id": user_id}), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn','').strip()
    user_id = request.form.get('user_id','').strip()
    if not isbn or not user_id:
        return jsonify({"status":"Error","message":"ISBN and user_id required"}), 400
    return jsonify({"status":"Book returned","isbn": isbn,"user_id": user_id}), 200

if __name__ == "__main__":
    app.run(debug=False)