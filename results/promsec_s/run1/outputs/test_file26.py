from flask import Flask, request, jsonify
import os
import re
from importlib import import_module
from yaml import safe_load

app = Flask(__name__)
LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must be a mapping'), 400
    required = {'title', 'author', 'isbn'}
    if not required.issubset(data):
        return jsonify(error='Missing required fields'), 400
    return jsonify(status='New Book added', title=data['title'], author=data['author'], isbn=data['isbn'])

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^[A-Za-z0-9_-]+$', section):
        return jsonify(error='Invalid section'), 400
    try:
        module = import_module('run_inventory')
        if not hasattr(module, 'main') or not callable(module.main):
            return jsonify(error='Invalid inventory module'), 500
        module.main(section)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(status='Inventory check started')

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify(status='Admin access granted')
    return jsonify(status='Access denied'), 401

if __name__ == '__main__':
    app.run(debug=False)