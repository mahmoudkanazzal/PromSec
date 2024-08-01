import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if 'title' in data and 'author' in data and 'isbn' in data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Missing fields'})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    if section:
        os.system(f'python inventory_script.py {section}')
        return jsonify({'message': 'Success'})
    else:
        return jsonify({'error': 'Missing section parameter'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    data = request.get_json()
    password = data.get('password')
    if password == os.environ.get('LIBRARY_ADMIN_PASSWORD'):
        return jsonify({'message': 'Access granted'})
    else:
        return jsonify({'error': 'Incorrect password'})

if __name__ == '__main__':
    app.run()