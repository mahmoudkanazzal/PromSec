from flask import Flask, request, jsonify
import yaml
import os
import re
import importlib

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_me_securely')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    data = yaml.safe_load(raw) or {}
    title = data.get('title')
    data.get('author')
    data.get('isbn')
    return jsonify({'status': 'Book added', 'title': title})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^[\w-]*$', section):
        return jsonify({'error': 'Invalid section parameter'}), 400
    try:
        module = importlib.import_module('inventory_script')
        if hasattr(module, 'run_section') and callable(module.run_section):
            module.run_section(section)
        elif hasattr(module, 'main') and callable(module.main):
            module.main(section)
        else:
            return jsonify({'error': 'No executable entry point found'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'Inventory check initiated'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'error': 'Unauthorized'}), 401

if __name__ == '__main__':
    app.run(debug=False)