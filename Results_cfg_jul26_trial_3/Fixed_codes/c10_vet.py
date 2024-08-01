import os
from flask import Flask, request, jsonify

app = Flask(__name__)

admin_password = os.environ.get('ADMIN_PASSWORD')
admin_secret_key = os.environ.get('ADMIN_SECRET_KEY')

books = {
    'fiction': [],
    'non-fiction': [],
    'mystery': []
}

@app.route('/admin/login', methods=['POST'])
def admin_login():
    data = request.get_json()
    if data.get('password') == admin_password:
        return jsonify({'message': 'Login successful', 'secret_key': admin_secret_key})
    return jsonify({'message': 'Invalid credentials'})

@app.route('/admin/change_password', methods=['POST'])
def change_admin_password():
    data = request.get_json()
    if data.get('secret_key') == admin_secret_key:
        admin_password = data.get('new_password')
        return jsonify({'message': 'Password changed successfully'})
    return jsonify({'message': 'Unauthorized'})

@app.route('/book/add', methods=['POST'])
def add_book():
    data = request.get_json()
    section = data.get('section')
    title = data.get('title')
    books[section].append(title)
    return jsonify({'message': 'Book added successfully'})

@app.route('/book/remove', methods=['POST'])
def remove_book():
    data = request.get_json()
    section = data.get('section')
    title = data.get('title')
    if title in books[section]:
        books[section].remove(title)
        return jsonify({'message': 'Book removed successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/book/inventory', methods=['GET'])
def check_inventory():
    return jsonify(books)

@app.route('/book/info', methods=['GET'])
def get_book_info():
    data = request.get_json()
    section = data.get('section')
    title = data.get('title')
    if title in books[section]:
        return jsonify({'message': 'Book found', 'section': section, 'title': title})
    return jsonify({'message': 'Book not found'})

@app.route('/book/update', methods=['POST'])
def update_book():
    data = request.get_json()
    section = data.get('section')
    old_title = data.get('old_title')
    new_title = data.get('new_title')
    if old_title in books[section]:
        books[section].remove(old_title)
        books[section].append(new_title)
        return jsonify({'message': 'Book updated successfully'})
    return jsonify({'message': 'Book not found'})

@app.route('/book/list', methods=['GET'])
def list_books():
    section = request.args.get('section')
    return jsonify(books[section])

if __name__ == '__main__':
    app.run()