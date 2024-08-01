import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARY = []

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('password') == LIBRARIAN_PASSWORD:
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid password'}), 401

@app.route('/books', methods=['GET'])
def list_books():
    return jsonify(LIBRARY)

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    LIBRARY.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    for book in LIBRARY:
        if book.get('id') == book_id:
            return jsonify(book)
    return jsonify({'message': 'Book not found'}), 404

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    for book in LIBRARY:
        if book.get('id') == book_id:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'}), 404

@app.route('/books/<int:book_id>', methods=['DELETE'])
def remove_book(book_id):
    for book in LIBRARY:
        if book.get('id') == book_id:
            LIBRARY.remove(book)
            return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'}), 404

if __name__ == '__main__':
    app.run()
