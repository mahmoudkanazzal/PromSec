from flask import Flask, request, jsonify
import os

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    # Add book logic here
    return jsonify({'message': 'Book added successfully'})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    # Run inventory logic here with section as argument
    return jsonify({'message': 'Inventory checked for section: {}'.format(section)})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'message': 'Access granted'})
    else:
        return jsonify({'message': 'Access denied'})

if __name__ == '__main__':
    app.run()