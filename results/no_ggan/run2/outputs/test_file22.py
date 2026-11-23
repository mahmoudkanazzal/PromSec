import os
import re
import subprocess
from flask import Flask, request, jsonify
import yaml

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn
    })

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^[\w-]*$', section):
        return jsonify({'status': 'Invalid section parameter'}), 400
    try:
        subprocess.run(
            ['python', 'inventory_script.py', section],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
    except Exception:
        return jsonify({'status': 'Failed to start inventory check'}), 500
    return jsonify({'status': 'Inventory check initiated'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if LIBRARIAN_PASSWORD is None:
        return jsonify({'status': 'Access denied'}), 401
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)