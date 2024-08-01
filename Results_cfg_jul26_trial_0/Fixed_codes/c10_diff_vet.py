import os
from flask import Flask, request, jsonify

app = Flask(__name__)

books = []

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/remove_book', methods=['DELETE'])
def remove_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            books.remove(book)
            return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/update_book', methods=['PUT'])
def update_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book.update(data)
            return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/list_books', methods=['GET'])
def list_books():
    return jsonify(books)

@app.route('/check_availability', methods=['GET'])
def check_availability():
    title = request.args.get('title')
    for book in books:
        if book['title'] == title:
            return jsonify({'available': book['available']})
    return jsonify({'message': 'Book not found'})

@app.route('/request_book', methods=['POST'])
def request_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            if book['available']:
                book['available'] = False
                return jsonify({'message': 'Book requested successfully'})
            else:
                return jsonify({'message': 'Book not available'})
    return jsonify({'message': 'Book not found'})

@app.route('/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['available'] = True
            return jsonify({'message': 'Book returned successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['review'] = data['review']
            return jsonify({'message': 'Review submitted successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/submit_event', methods=['POST'])
def submit_event():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['event'] = data['event']
            return jsonify({'message': 'Event submitted successfully'})
    return jsonify({'message': 'Book not found'})

admin_password = os.getenv('ADMIN_PASSWORD')

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data['password'] == admin_password:
        return jsonify({'message': 'Admin login successful'})
    return jsonify({'message': 'Invalid password'})

@app.route('/change_admin_password', methods=['PUT'])
def change_admin_password():
    data = request.get_json()
    global admin_password
    admin_password = data['new_password']
    return jsonify({'message': 'Admin password changed successfully'})

if __name__ == '__main__':
    app.run()