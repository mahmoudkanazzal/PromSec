import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARY = {
    "fiction": [],
    "non-fiction": []
}

LIBRARIAN_PASSWORD = os.getenv("LIBRARIAN_PASSWORD", "super_secret_pass_2024")

def is_authenticated(password):
    return password == LIBRARIAN_PASSWORD

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    password = data.get('password')
    if is_authenticated(password):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Login failed"})

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if is_authenticated(old_password):
        global LIBRARIAN_PASSWORD
        LIBRARIAN_PASSWORD = new_password
        return jsonify({"message": "Password changed successfully"})
    else:
        return jsonify({"message": "Invalid old password"})

@app.route('/library/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    section = data.get('section')
    title = data.get('title')
    author = data.get('author')
    LIBRARY[section].append({"title": title, "author": author})
    return jsonify({"message": "Book added successfully"})

@app.route('/library/remove_book', methods=['POST'])
def remove_book():
    data = request.get_json()
    section = data.get('section')
    title = data.get('title')
    for book in LIBRARY[section]:
        if book['title'] == title:
            LIBRARY[section].remove(book)
            return jsonify({"message": "Book removed successfully"})
    return jsonify({"message": "Book not found"})

@app.route('/library/check_inventory', methods=['GET'])
def check_inventory():
    return jsonify(LIBRARY)

@app.route('/library/book_info', methods=['GET'])
def book_info():
    section = request.args.get('section')
    title = request.args.get('title')
    for book in LIBRARY[section]:
        if book['title'] == title:
            return jsonify(book)
    return jsonify({"message": "Book not found"})

@app.route('/library/update_book', methods=['PUT'])
def update_book():
    data = request.get_json()
    section = data.get('section')
    title = data.get('title')
    new_author = data.get('author')
    for book in LIBRARY[section]:
        if book['title'] == title:
            book['author'] = new_author
            return jsonify({"message": "Book updated successfully"})
    return jsonify({"message": "Book not found"})

@app.route('/library/list_books', methods=['GET'])
def list_books():
    section = request.args.get('section')
    return jsonify(LIBRARY[section])

if __name__ == '__main__':
    app.run()