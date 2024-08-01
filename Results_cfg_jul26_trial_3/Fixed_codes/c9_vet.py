import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
LIBRARY = {}

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
    title = data.get('title')
    author = data.get('author')
    quantity = data.get('quantity')
    LIBRARY[title] = {'author': author, 'quantity': quantity}
    return jsonify({'message': 'Book added successfully'})

@app.route('/books/remove', methods=['POST'])
def remove_book():
    data = request.get_json()
    title = data.get('title')
    if title in LIBRARY:
        del LIBRARY[title]
        return jsonify({'message': 'Book removed successfully'})
    else:
        return jsonify({'message': 'Book not found'})

@app.route('/books/list', methods=['GET'])
def list_books():
    return jsonify(LIBRARY)

if __name__ == '__main__':
    app.run()