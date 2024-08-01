import os
from flask import Flask, request, jsonify

app = Flask(__name__)

admin_password = os.environ.get('ADMIN_PASSWORD')

books = []
members = []

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/inventory_check', methods=['GET'])
def inventory_check():
    return jsonify({'total_books': len(books)})

@app.route('/grant_admin_access', methods=['POST'])
def grant_admin_access():
    data = request.get_json()
    if 'password' in data and data['password'] == admin_password:
        return jsonify({'message': 'Admin access granted'})
    else:
        return jsonify({'message': 'Invalid password'})

@app.route('/update_book_details', methods=['PUT'])
def update_book_details():
    data = request.get_json()
    for book in books:
        if book['id'] == data['id']:
            book.update(data)
            return jsonify({'message': 'Book details updated'})
    return jsonify({'message': 'Book not found'})

@app.route('/delete_book', methods=['DELETE'])
def delete_book():
    data = request.get_json()
    for book in books:
        if book['id'] == data['id']:
            books.remove(book)
            return jsonify({'message': 'Book deleted'})
    return jsonify({'message': 'Book not found'})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    # Generate reports logic here
    return jsonify({'message': 'Reports generated'})

@app.route('/librarian_panel', methods=['GET'])
def librarian_panel():
    # Librarian panel logic here
    return jsonify({'message': 'Welcome to librarian panel'})

@app.route('/view_books', methods=['GET'])
def view_books():
    return jsonify({'books': books})

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.get_json()
    members.append(data)
    return jsonify({'message': 'Member added successfully'})

@app.route('/update_member_details', methods=['PUT'])
def update_member_details():
    data = request.get_json()
    for member in members:
        if member['id'] == data['id']:
            member.update(data)
            return jsonify({'message': 'Member details updated'})
    return jsonify({'message': 'Member not found'})

if __name__ == '__main__':
    app.run()
