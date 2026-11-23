from flask import Flask, request, jsonify
import os
import importlib
import re
from yaml import safe_load

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    raw = request.get_data(as_text=True)
    try:
        data = safe_load(raw)
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    return jsonify({"status": "New Book added", "title": title, "author": author, "isbn": isbn}), 200

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'\w*', section):
        return jsonify({"status": "Error", "message": "Invalid section parameter"}), 400
    try:
        module = importlib.import_module('run_inventory')
        if not hasattr(module, 'main'):
            return jsonify({"status": "Error", "message": "run_inventory module lacks a main function"}), 500
        module.main(section)
    except Exception:
        return jsonify({"status": "Error", "message": "Failed to start inventory check"}), 500
    return jsonify({"status": "Inventory check started"}), 200

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if LIBRARIAN_PASSWORD and password == LIBRARIAN_PASSWORD:
        return jsonify({"status": "Admin access granted"}), 200
    return jsonify({"status": "Access denied"}), 401

if __name__ == '__main__':
    app.run(debug=False)