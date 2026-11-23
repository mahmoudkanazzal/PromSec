import os
import re
import hmac
from flask import Flask, request, jsonify
import yaml
from importlib import import_module

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_me_securely')
app = Flask(__name__)

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    raw = request.get_data()
    try:
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Missing required book fields"}), 400
    return jsonify({"status": "New Book added", "title": title, "author": author, "isbn": isbn}), 200

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section')
    if section is not None:
        if not re.fullmatch(r'\w+', section):
            return jsonify({"status": "Error", "message": "Invalid section parameter"}), 400
    try:
        inventory_module = import_module('run_inventory')
        if not hasattr(inventory_module, 'main'):
            return jsonify({"status": "Error", "message": "Inventory module missing entry point"}), 500
        if section is not None:
            inventory_module.main(section)
        else:
            inventory_module.main()
    except Exception:
        return jsonify({"status": "Error", "message": "Failed to start inventory"}), 500
    return jsonify({"status": "Inventory check started"}), 200

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({"status": "Admin access granted"}), 200
    else:
        return jsonify({"status": "Access denied"}), 401

if __name__ == "__main__":
    app.run(debug=False)