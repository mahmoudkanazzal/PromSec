import os
from flask import Flask, request, jsonify

app = Flask(__name__)

books = []

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/remove_book', methods=['POST'])
def remove_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            books.remove(book)
            return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/update_book', methods=['POST'])
def update_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['author'] = data['author']
            book['genre'] = data['genre']
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/list_books', methods=['GET'])
def list_books():
    return jsonify(books)

@app.route('/check_availability', methods=['POST'])
def check_availability():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            return jsonify({'available': book['available']})
    return jsonify({'message': 'Book not found'})

@app.route('/request_book', methods=['POST'])
def request_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['available'] = False
            return jsonify({'message': 'Book requested successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['available'] = True
            return jsonify({'message': 'Book returned successfully'})
    return jsonify({'message': 'Book not found'})

if __name__ == '__main__':
    app.run()