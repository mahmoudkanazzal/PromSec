import os
import re
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

_lib_password = os.getenv('LIBRARIAN_PASSWORD')
if _lib_password is None:
    raise RuntimeError('Environment variable LIBRARIAN_PASSWORD must be set')
ADMIN_SECRET_KEY = os.getenv('ADMIN_SECRET_KEY')
if ADMIN_SECRET_KEY is None:
    raise RuntimeError('Environment variable ADMIN_SECRET_KEY must be set')
current_password = _lib_password

def json_error(message, status_code):
    return jsonify({"status":"Error","message":message}), status_code

@app.route('/library/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return json_error("Invalid YAML format",400)
    if not isinstance(data, dict):
        return json_error("Invalid YAML format",400)
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return json_error("Missing required fields",400)
    publisher = data.get('publisher', "Unknown")
    year = data.get('year_published', "Unknown")
    if year != "Unknown":
        try:
            year = int(year)
        except Exception:
            return json_error("year_published must be an integer",400)
    return jsonify({"status":"Book added","title":title,"author":author,"isbn":isbn,"publisher":publisher,"year_published":year}), 200

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return json_error("ISBN missing",400)
    return jsonify({"status":"Book removed","isbn":isbn}), 200

@app.route('/inventory/check', methods=['GET'])
def inventory_check():
    section = request.args.get('section')
    location = request.args.get('location')
    if not section or not location:
        return json_error("Missing parameters",400)
    if not re.fullmatch(r'[\w\-]+', section) or not re.fullmatch(r'[\w\-]+', location):
        return json_error("Invalid parameters",400)
    return jsonify({"status":"Inventory check started"}), 200

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password')
    secret_key = request.form.get('secret_key')
    if password == current_password and secret_key == ADMIN_SECRET_KEY:
        return jsonify({"status":"Admin access granted","message":"Welcome, Admin!"}), 200
    return jsonify({"status":"Access denied","message":"Invalid credentials"}), 401

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    global current_password
    old_password = request.form.get('old_password')
    new_password = request.form.get('new_password')
    if old_password == current_password:
        current_password = new_password if new_password is not None else ''
        return jsonify({"status":"Password changed successfully"}), 200
    return jsonify({"status":"Access denied","message":"Invalid old password"}), 401

@app.route('/library/book_info', methods=['GET'])
def book_info():
    isbn = request.args.get('isbn')
    if not isbn:
        return json_error("ISBN missing",400)
    return jsonify({"status":"Book details","isbn":isbn,"title":"Sample Title","author":"Sample Author","publisher":"Sample Publisher","year_published":"Unknown"}), 200

@app.route('/library/update_book', methods=['POST'])
def update_book():
    isbn = request.form.get('isbn')
    if not isbn:
        return json_error("ISBN missing",400)
    new_title = request.form.get('new_title')
    new_author = request.form.get('new_author')
    return jsonify({"status":"Book updated","isbn":isbn,"new_title":new_title,"new_author":new_author}), 200

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    books = [{"title":"Book One","author":"Author A","isbn":"111"},{"title":"Book Two","author":"Author B","isbn":"222"}]
    return jsonify({"status":"Books listed","section":section,"books":books}), 200

@app.route('/api/check_availability', methods=['GET'])
def check_availability():
    isbn = request.args.get('isbn')
    if not isbn:
        return json_error("ISBN missing",400)
    return jsonify({"status":"Book availability","isbn":isbn,"available":True}), 200

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return json_error("Missing parameters",400)
    return jsonify({"status":"Book requested","isbn":isbn,"user_id":user_id}), 200

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn')
    user_id = request.form.get('user_id')
    if not isbn or not user_id:
        return json_error("Missing parameters",400)
    return jsonify({"status":"Book returned","isbn":isbn,"user_id":user_id}), 200

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return json_error("Invalid YAML format",400)
    if not isinstance(data, dict):
        return json_error("Invalid YAML format",400)
    isbn = data.get('isbn')
    user_id = data.get('user_id')
    review_text = data.get('review_text')
    if not isbn or not user_id or not review_text:
        return json_error("Missing required fields",400)
    rating = data.get('rating')
    if rating is not None:
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except Exception:
            return json_error("Invalid rating",400)
    return jsonify({"status":"Review submitted","isbn":isbn,"user_id":user_id,"review_text":review_text,"rating":rating}), 200

@app.route('/api/submit_event', methods=['POST'])
def submit_event():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except Exception:
        return json_error("Invalid YAML format",400)
    if not isinstance(data, dict):
        return json_error("Invalid YAML format",400)
    event_id = data.get('event_id')
    event_name = data.get('event_name')
    event_date = data.get('event_date')
    if not event_id or not event_name or not event_date:
        return json_error("Missing required fields",400)
    return jsonify({"status":"Event submitted","event_id":event_id,"event_name":event_name,"event_date":event_date}), 200

if __name__ == '__main__':
    app.run(debug=False)