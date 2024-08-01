import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

books = []

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if 'password' in data and data['password'] == LIBRARIAN_PASSWORD:
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Login failed'})

@app.route('/admin/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    if 'password' in data:
        global LIBRARIAN_PASSWORD
        LIBRARIAN_PASSWORD = data['password']
        return jsonify({'message': 'Password changed successfully'})
    return jsonify({'message': 'Password change failed'})

@app.route('/books/add', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/remove', methods=['POST'])
def remove_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            books.remove(book)
            return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/inventory', methods=['GET'])
def check_inventory():
    return jsonify(books)

@app.route('/books/update', methods=['PUT'])
def update_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/info', methods=['GET'])
def get_book_info():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            return jsonify(book)
    return jsonify({'message': 'Book not found'})

@app.route('/books/list', methods=['GET'])
def list_books():
    return jsonify(books)

if __name__ == '__main__':
    app.run()