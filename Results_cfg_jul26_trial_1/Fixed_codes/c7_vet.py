import os
from flask import Flask, request, jsonify

app = Flask(__name__)

books = []

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    books.append(data)
    return jsonify({'message': 'Book added successfully'})

@app.route('/run_inventory_script', methods=['GET'])
def run_inventory_script():
    if request.headers.get('Authorization') == os.environ.get('INVENTORY_SCRIPT_KEY'):
        # Run inventory script logic here
        return jsonify({'message': 'Inventory script executed'})
    else:
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/grant_librarian_access', methods=['POST'])
def grant_librarian_access():
    data = request.get_json()
    if data.get('password') == os.environ.get('LIBRARIAN_PASSWORD'):
        # Grant librarian access logic here
        return jsonify({'message': 'Librarian access granted'})
    else:
        return jsonify({'error': 'Incorrect password'}), 401

if __name__ == '__main__':
    app.run()