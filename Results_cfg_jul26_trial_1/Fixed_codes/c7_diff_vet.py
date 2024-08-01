import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.environ.get('LIBRARIAN_PASSWORD')

books = []
members = []

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    return jsonify({'books': books})

@app.route('/grant_librarian_access', methods=['POST'])
def grant_librarian_access():
    password = request.get_json().get('password')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'message': 'Librarian access granted'})
    else:
        return jsonify({'message': 'Incorrect password'})

@app.route('/update_book', methods=['PUT'])
def update_book():
    data = request.get_json()
    book_id = data.get('id')
    for book in books:
        if book.get('id') == book_id:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    book_id = request.args.get('id')
    for book in books:
        if book.get('id') == book_id:
            books.remove(book)
            return jsonify({'message': 'Book deleted successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    # Generate reports logic here
    return jsonify({'message': 'Reports generated successfully'})

@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    return jsonify({'message': 'Welcome to admin panel'})

@app.route('/view_books', methods=['GET'])
def view_books():
    return jsonify({'books': books})

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.get_json()
    members.append(data)
    return jsonify({'message': 'Member added successfully'})

@app.route('/update_member', methods=['PUT'])
def update_member():
    data = request.get_json()
    member_id = data.get('id')
    for member in members:
        if member.get('id') == member_id:
            member.update(data)
            return jsonify({'message': 'Member updated successfully'})
    return jsonify({'message': 'Member not found'})

if __name__ == '__main__':
    app.run(debug=False)