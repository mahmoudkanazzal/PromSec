import os
from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_json()
    if 'title' in data and 'author' in data and 'isbn' in data:
        return jsonify(data)
    else:
        return jsonify({'error': 'Missing required keys'})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    subprocess.run(['python', 'inventory_script.py', section])
    return jsonify({'message': f'Processed section: {section}'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.json.get('password')
    if password == os.environ.get('LIBRARY_PASSWORD'):
        return 'Access granted'
    else:
        return 'Access denied'

if __name__ == '__main__':
    app.run()