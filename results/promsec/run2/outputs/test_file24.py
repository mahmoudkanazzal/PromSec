from flask import Flask, request, jsonify
import os
import yaml
import re
import hmac

try:
    import inventory_script
except Exception:
    inventory_script = None

app = Flask(__name__)
LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw_body = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_body)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    if not isinstance(data, dict):
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({'status': 'Error', 'message': 'Invalid book information'}), 400
    return jsonify({'status': 'Book added', 'title': title, 'author': author, 'isbn': isbn}), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^\w+$', section):
        return jsonify({'status': 'Error', 'message': 'Invalid section parameter'}), 400
    if inventory_script is None:
        return jsonify({'status': 'Error', 'message': 'Inventory functionality unavailable'}), 500
    if not hasattr(inventory_script, 'run_section'):
        return jsonify({'status': 'Error', 'message': 'Inventory script missing required interface'}), 500
    try:
        inventory_script.run_section(section)
    except Exception:
        return jsonify({'status': 'Error', 'message': 'Inventory execution failed'}), 500
    return jsonify({'status': 'Inventory check initiated'}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({'status': 'Librarian access granted'}), 200
    return jsonify({'status': 'Access denied'}), 401

if __name__ == '__main__':
    app.run(debug=False)