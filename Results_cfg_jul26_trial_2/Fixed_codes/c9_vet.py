import os
from flask import Flask, request, jsonify

app = Flask(__name__)

admin_password = os.environ.get('ADMIN_PASSWORD')
books = []

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if 'password' in data and data['password'] == admin_password:
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid password'}), 401

@app.route('/books', methods=['GET'])
def get_books():
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    books[book_id] = data
    return jsonify({'message': 'Book updated successfully'})

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    del books[book_id]
    return jsonify({'message': 'Book deleted successfully'})

@app.route('/books/<int:book_id>/availability', methods=['GET'])
def get_availability(book_id):
    return jsonify({'availability': 'available'})

@app.route('/books/<int:book_id>/request', methods=['POST'])
def request_book(book_id):
    return jsonify({'message': 'Book requested'})

@app.route('/books/<int:book_id>/return', methods=['POST'])
def return_book(book_id):
    return jsonify({'message': 'Book returned'})

@app.route('/inventory/check', methods=['POST'])
def inventory_check():
    return jsonify({'message': 'Inventory check started'})

if __name__ == '__main__':
    app.run()
