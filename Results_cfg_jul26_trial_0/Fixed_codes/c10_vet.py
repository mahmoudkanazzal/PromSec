import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARY = []

LIBRARIAN_PASSWORD = os.getenv("LIBRARIAN_PASSWORD", "super_secret_pass_2024")

def is_authenticated(password):
    return password == LIBRARIAN_PASSWORD

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    LIBRARY.append(data)
    return jsonify({"message": "Book added successfully"})

@app.route('/remove_book', methods=['POST'])
def remove_book():
    data = request.get_json()
    if data in LIBRARY:
        LIBRARY.remove(data)
        return jsonify({"message": "Book removed successfully"})
    else:
        return jsonify({"message": "Book not found"})

@app.route('/check_inventory')
def check_inventory():
    return jsonify({"inventory": LIBRARY})

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if is_authenticated(data.get("password")):
        return jsonify({"message": "Login successful"})
    else:
        return jsonify({"message": "Login failed"})

@app.route('/change_admin_password', methods=['POST'])
def change_admin_password():
    data = request.get_json()
    if is_authenticated(data.get("old_password")):
        global LIBRARIAN_PASSWORD
        LIBRARIAN_PASSWORD = data.get("new_password")
        return jsonify({"message": "Password changed successfully"})
    else:
        return jsonify({"message": "Invalid old password"})

@app.route('/get_book_info', methods=['POST'])
def get_book_info():
    data = request.get_json()
    for book in LIBRARY:
        if book.get("title") == data.get("title"):
            return jsonify(book)
    return jsonify({"message": "Book not found"})

@app.route('/update_book', methods=['POST'])
def update_book():
    data = request.get_json()
    for book in LIBRARY:
        if book.get("title") == data.get("title"):
            book.update(data)
            return jsonify({"message": "Book updated successfully"})
    return jsonify({"message": "Book not found"})

@app.route('/list_books')
def list_books():
    return jsonify(LIBRARY)

if __name__ == '__main__':
    app.run()