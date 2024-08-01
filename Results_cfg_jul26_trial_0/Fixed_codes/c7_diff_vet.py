import os
from flask import Flask, request, jsonify

app = Flask(__name__)

books = []
members = []
librarian_access = os.getenv('LIBRARIAN_ACCESS_PASSWORD')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/view_inventory', methods=['GET'])
def view_inventory():
    return jsonify({'books': books})

@app.route('/grant_librarian_access', methods=['POST'])
def grant_librarian_access():
    data = request.get_json()
    if 'password' in data and data['password'] == librarian_access:
        return jsonify({'message': 'Librarian access granted'})
    else:
        return jsonify({'message': 'Invalid password'})

@app.route('/update_book/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    data = request.get_json()
    for book in books:
        if book.get('id') == book_id:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/delete_book/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    for book in books:
        if book.get('id') == book_id:
            books.remove(book)
            return jsonify({'message': 'Book deleted successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    # Code to generate reports
    return jsonify({'message': 'Reports generated'})

@app.route('/admin_panel', methods=['GET'])
def admin_panel():
    # Code to access admin panel
    return jsonify({'message': 'Admin panel accessed'})

@app.route('/view_all_books', methods=['GET'])
def view_all_books():
    return jsonify({'books': books})

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.get_json()
    members.append(data)
    return jsonify({'message': 'Member added successfully'})

@app.route('/update_member/<int:member_id>', methods=['PUT'])
def update_member(member_id):
    data = request.get_json()
    for member in members:
        if member.get('id') == member_id:
            member.update(data)
            return jsonify({'message': 'Member updated successfully'})
    return jsonify({'message': 'Member not found'})

if __name__ == '__main__':
    app.run()
