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
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/books/add', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/remove', methods=['POST'])
def remove_book():
    data = request.get_json()
    title = data.get('title')
    for book in books:
        if book.get('title') == title:
            books.remove(book)
            return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/list', methods=['GET'])
def list_books():
    return jsonify(books)

@app.route('/books/update', methods=['PUT'])
def update_book():
    data = request.get_json()
    title = data.get('title')
    for book in books:
        if book.get('title') == title:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/info', methods=['GET'])
def get_book_info():
    title = request.args.get('title')
    for book in books:
        if book.get('title') == title:
            return jsonify(book)
    return jsonify({'message': 'Book not found'})

if __name__ == '__main__':
    app.run()