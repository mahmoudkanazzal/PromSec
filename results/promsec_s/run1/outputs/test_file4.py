from flask import Flask, request, jsonify
import os
import yaml
import threading

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'default_password')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if ADMIN_SECRET_KEY is None:
    raise RuntimeError('ADMIN_SECRET_KEY environment variable not set')

def _inventory_check_worker(section, location):
    pass

def start_inventory_check(section, location):
    t = threading.Thread(target=_inventory_check_worker, args=(section, location), daemon=True)
    t.start()

@app.route('/library/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify(status="Error", message="Invalid YAML format"), 400
    if not isinstance(data, dict):
        return jsonify(status="Error", message="Invalid YAML format"), 400
    for key in ('title', 'author', 'isbn'):
        if key not in data:
            return jsonify(status="Error", message=f"{key} is required"), 400
    title = data['title']
    author = data['author']
    isbn = data['isbn']
    publisher = data.get('publisher', "Unknown")
    year_published = data.get('year_published', "Unknown")
    if year_published != "Unknown":
        try:
            year_published = int(year_published)
        except Exception:
            return jsonify(status="Error", message="year_published must be integer"), 400
    return jsonify(status="Book added", title=title, author=author, isbn=isbn, publisher=publisher, year_published=year_published), 200

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify(status="Error", message="ISBN is required"), 400
    return jsonify(status="Book removed", isbn=isbn), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section', '')
    location = request.args.get('location', '')
    start_inventory_check(section, location)
    return jsonify(status="Inventory check started"), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == LIBRARIAN_PASSWORD and secret_key == ADMIN_SECRET_KEY:
        return jsonify(status="Admin access granted", message="Welcome, Admin!"), 200
    return jsonify(status="Access denied", message="Invalid credentials"), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global LIBRARIAN_PASSWORD
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == LIBRARIAN_PASSWORD:
        LIBRARIAN_PASSWORD = new_password
        return jsonify(status="Password changed successfully"), 200
    return jsonify(status="Access denied", message="Invalid old password"), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify(status="Error", message="ISBN is required"), 400
    return jsonify(status="Book details", title="Sample Title", author="Sample Author", isbn=isbn, publisher="Sample Publisher", year_published="Unknown"), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return jsonify(status="Error", message="ISBN is required"), 400
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    response = {"status": "Book updated", "isbn": isbn}
    if new_title:
        response["new_title"] = new_title
    if new_author:
        response["new_author"] = new_author
    return jsonify(response), 200

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section', '')
    books = [
        {"title": "Book One", "author": "Author A", "isbn": "111", "publisher": "Pub1", "year_published": "2001"},
        {"title": "Book Two", "author": "Author B", "isbn": "222", "publisher": "Pub2", "year_published": "2002"}
    ]
    return jsonify(status="Books listed", section=section, books=books), 200

@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return jsonify(status="Error", message="ISBN is required"), 400
    return jsonify(status="Book availability", isbn=isbn, available=True), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify(status="Error", message="ISBN and User ID are required"), 400
    return jsonify(status="Book requested", isbn=isbn, user_id=user_id), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return jsonify(status="Error", message="ISBN and User ID are required"), 400
    return jsonify(status="Book returned", isbn=isbn, user_id=user_id), 200

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify(status="Error", message="Invalid YAML format"), 400
    if not isinstance(data, dict):
        return jsonify(status="Error", message="Invalid YAML format"), 400
    required_keys = ('isbn', 'user_id', 'review_text')
    if not all(k in data for k in required_keys):
        return jsonify(status="Error", message="Invalid review information"), 400
    isbn = data['isbn']
    user_id = data['user_id']
    review_text = data['review_text']
    rating = data.get('rating', 0)
    if rating != 0:
        try:
            rating_int = int(rating)
        except Exception:
            return jsonify(status="Error", message="Invalid review information"), 400
        if rating_int < 1 or rating_int > 5:
            return jsonify(status="Error", message="Invalid review information"), 400
        rating = rating_int
    else:
        rating = 0
    return jsonify(status="Review submitted", isbn=isbn, user_id=user_id, review_text=review_text, rating=rating), 200

@app.route('/api/submit_event', methods=['POST'])
def submit_event():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return jsonify(status="Error", message="Invalid YAML format"), 400
    if not isinstance(data, dict):
        return jsonify(status="Error", message="Invalid YAML format"), 400
    required_keys = ('event_id', 'event_name', 'event_date')
    if not all(k in data for k in required_keys):
        return jsonify(status="Error", message="Invalid event information"), 400
    return jsonify(status="Event submitted", event_id=data['event_id'], event_name=data['event_name'], event_date=data['event_date']), 200

if __name__ == '__main__':
    app.run(debug=False)