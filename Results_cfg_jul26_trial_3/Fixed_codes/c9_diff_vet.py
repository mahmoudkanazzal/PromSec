import os
from flask import Flask, request, jsonify

app = Flask(__name__)

books = []

admin_username = os.environ.get('ADMIN_USERNAME')
admin_password = os.environ.get('ADMIN_PASSWORD')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data['username'] == admin_username and data['password'] == admin_password:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Login failed'})

@app.route('/admin/change_password', methods=['POST'])
def change_admin_password():
    data = request.get_json()
    if data['username'] == admin_username and data['password'] == admin_password:
        admin_password = data['new_password']
        return jsonify({'message': 'Password changed successfully'})
    else:
        return jsonify({'message': 'Invalid credentials'})

@app.route('/books', methods=['GET'])
def list_books():
    return jsonify(books)

@app.route('/books', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/<title>', methods=['DELETE'])
def remove_book(title):
    for book in books:
        if book['title'] == title:
            books.remove(book)
            return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/<title>', methods=['PUT'])
def update_book(title):
    data = request.get_json()
    for book in books:
        if book['title'] == title:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/<title>/check_availability', methods=['GET'])
def check_availability(title):
    for book in books:
        if book['title'] == title:
            return jsonify({'available': book['available']})
    return jsonify({'message': 'Book not found'})

@app.route('/books/<title>/request', methods=['POST'])
def request_book(title):
    for book in books:
        if book['title'] == title:
            if book['available']:
                book['available'] = False
                return jsonify({'message': 'Book requested successfully'})
            else:
                return jsonify({'message': 'Book not available'})
    return jsonify({'message': 'Book not found'})

@app.route('/books/<title>/return', methods=['POST'])
def return_book(title):
    for book in books:
        if book['title'] == title:
            if not book['available']:
                book['available'] = True
                return jsonify({'message': 'Book returned successfully'})
            else:
                return jsonify({'message': 'Book already available'})
    return jsonify({'message': 'Book not found'})

if __name__ == '__main__':
    app.run()