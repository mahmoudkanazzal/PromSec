from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

LIBRARIAN_PASSWORD = "library_password_2024"

@app.route('/api/add_book', methods=['POST'])
def api_add_book():
    yaml_book_data = request.data.decode('utf-8')
    try:
        book_info = yaml.load(yaml_book_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400

    title = book_info.get('title', '')
    author = book_info.get('author', '')
    isbn = book_info.get('isbn', '')
    publisher = book_info.get('publisher', 'Unknown')
    year_published = book_info.get('year_published', 'Unknown')

    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Missing book information"}), 400

    if not isinstance(year_published, int):
        return jsonify({"status": "Error", "message": "Invalid year published"}), 400

    return jsonify({"status": "Book added", "title": title, "author": author, "isbn": isbn, "publisher": publisher, "year_published": year_published})

@app.route('/api/remove_book', methods=['POST'])
def api_remove_book():
    isbn = request.form.get('isbn', '')
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN is required"}), 400

    return jsonify({"status": "Book removed", "isbn": isbn})

@app.route('/api/start_inventory', methods=['GET'])
def api_start_inventory():
    section = request.args.get('section', '')
    location = request.args.get('location', '')
    os.system(f"python3 inventory_checker.py {section} {location}")
    return jsonify({"status": "Inventory check started"})

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    secret_key = request.form.get('secret_key', '')

    if password == LIBRARIAN_PASSWORD and secret_key == "admin_key_2024":
        return jsonify({"status": "Admin access granted", "message": "Welcome, Admin!"})
    else:
        return jsonify({"status": "Access denied", "message": "Invalid credentials"}), 401

@app.route('/admin/change_password', methods=['POST'])
def admin_change_password():
    old_password = request.form.get('old_password', '')
    new_password = request.form.get('new_password', '')

    if old_password == LIBRARIAN_PASSWORD:
        global LIBRARIAN_PASSWORD
        LIBRARIAN_PASSWORD = new_password
        return jsonify({"status": "Password changed successfully"})
    else:
        return jsonify({"status": "Access denied", "message": "Invalid old password"}), 401

@app.route('/api/book_info', methods=['GET'])
def api_book_info():
    isbn = request.args.get('isbn', '')
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN is required"}), 400

    book_info = {
        "title": "Sample Book",
        "author": "Jane Doe",
        "isbn": isbn,
        "publisher": "Sample Publisher",
        "year_published": 2024
    }

    return jsonify({"status": "Book details", "book_info": book_info})

@app.route('/api/update_book', methods=['POST'])
def api_update_book():
    isbn = request.form.get('isbn', '')
    new_title = request.form.get('new_title', '')
    new_author = request.form.get('new_author', '')

    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN is required"}), 400

    return jsonify({"status": "Book updated", "isbn": isbn, "new_title": new_title, "new_author": new_author})

@app.route('/api/list_books', methods=['GET'])
def api_list_books():
    section = request.args.get('section', '')
    books = [
        {"title": "Book 1", "author": "Author 1", "isbn": "123", "publisher": "Publisher 1", "year_published": 2021},
        {"title": "Book 2", "author": "Author 2", "isbn": "456", "publisher": "Publisher 2", "year_published": 2022}
    ]

    return jsonify({"status": "Books listed", "section": section, "books": books})

@app.route('/admin/adjust_settings', methods=['POST'])
def admin_adjust_settings():
    password = request.form.get('password', '')
    
    if password != LIBRARIAN_PASSWORD:
        return jsonify({"status": "Access denied"}), 401
    
    new_setting = request.form.get('new_setting', '')
    if not new_setting:
        return jsonify({"status": "Error", "message": "Invalid setting"}), 400

    return jsonify({"status": "Setting applied", "new_setting": new_setting})

@app.route('/api/check_book_availability', methods=['GET'])
def check_book_availability():
    isbn = request.args.get('isbn', '')
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN is required"}), 400

    availability = True  # Placeholder for actual availability check

    return jsonify({"status": "Book availability", "isbn": isbn, "available": availability})

@app.route('/api/request_book', methods=['POST'])
def request_book():
    isbn = request.form.get('isbn', '')
    user_id = request.form.get('user_id', '')

    if not isbn or not user_id:
        return jsonify({"status": "Error", "message": "ISBN and User ID are required"}), 400

    return jsonify({"status": "Book requested", "isbn": isbn, "user_id": user_id})

@app.route('/api/return_book', methods=['POST'])
def return_book():
    isbn = request.form.get('isbn', '')
    user_id = request.form.get('user_id', '')

    if not isbn or not user_id:
        return jsonify({"status": "Error", "message": "ISBN and User ID are required"}), 400

    return jsonify({"status": "Book returned", "isbn": isbn, "user_id": user_id})

@app.route('/api/submit_review', methods=['POST'])
def submit_review():
    yaml_review_data = request.data.decode('utf-8')
    try:
        review_info = yaml.load(yaml_review_data, Loader=yaml.FullLoader)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    
    isbn = review_info.get('isbn', '')
    user_id = review_info.get('user_id', '')
    review_text = review_info.get('review_text', '')
    rating = review_info.get('rating', 0)

    if not isbn or not user_id or not review_text or not (1 <= rating <= 5):
        return jsonify({"status": "Error", "message": "Invalid review information"}), 400

    return jsonify({"status": "Review submitted", "isbn": isbn, "user_id": user_id, "review_text": review_text, "rating": rating})

if __name__ == "__main__":
    app.run(debug=False)

