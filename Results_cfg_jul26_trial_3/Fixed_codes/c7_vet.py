import os
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    return jsonify(data)

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    if section.isalnum():
        os.system(f'python inventory_script.py {section}')
        return jsonify({'message': 'Inventory script executed'})
    else:
        return jsonify({'message': 'Invalid section provided'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    data = request.get_json()
    if 'password' in data and data['password'] == LIBRARIAN_PASSWORD:
        return jsonify({'message': 'Access granted'})
    else:
        return jsonify({'message': 'Access denied'})

if __name__ == '__main__':
    app.run()