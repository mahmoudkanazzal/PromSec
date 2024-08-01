from flask import Flask, request

app = Flask(__name__)

books = []

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return "Book added successfully"

@app.route('/remove_book', methods=['DELETE'])
def remove_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            books.remove(book)
            return "Book removed successfully"
    return "Book not found"

@app.route('/update_book', methods=['PUT'])
def update_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book.update(data)
            return "Book updated successfully"
    return "Book not found"

@app.route('/list_books', methods=['GET'])
def list_books():
    return {'books': books}

@app.route('/check_inventory', methods=['GET'])
def check_inventory():
    return {'total_books': len(books)}

@app.route('/admin_login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data['username'] == 'admin' and data['password'] == 'admin123':
        return "Login successful"
    return "Invalid credentials"

@app.route('/change_password', methods=['PUT'])
def change_password():
    data = request.get_json()
    if data['username'] == 'admin':
        return "Password changed successfully"
    return "Invalid username"

@app.route('/book_info', methods=['GET'])
def book_info():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            return book
    return "Book not found"

@app.route('/book_availability', methods=['GET'])
def book_availability():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            return {'available': book['available']}
    return "Book not found"

@app.route('/request_book', methods=['POST'])
def request_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            if book['available']:
                book['available'] = False
                return "Book requested successfully"
            else:
                return "Book not available"
    return "Book not found"

@app.route('/return_book', methods=['POST'])
def return_book():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['available'] = True
            return "Book returned successfully"
    return "Book not found"

@app.route('/submit_review', methods=['POST'])
def submit_review():
    data = request.get_json()
    for book in books:
        if book['title'] == data['title']:
            book['reviews'].append(data['review'])
            return "Review submitted successfully"
    return "Book not found"

@app.route('/submit_event', methods=['POST'])
def submit_event():
    data = request.get_json()
    books.append(data)
    return "Event added successfully"

if __name__ == '__main__':
    app.run()