import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify, abort
from werkzeug.security import check_password_hash

LIBRARIAN_PASSWORD_HASH = os.getenv('LIBRARIAN_PASSWORD_HASH')
if not LIBRARIAN_PASSWORD_HASH:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD_HASH must be set for authentication.")

SECTION_PATTERN = re.compile(r'^[A-Za-z0-9_]+$')

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    title = str(data.get('title', '')).strip()
    author = str(data.get('author', '')).strip()
    isbn = str(data.get('isbn', '')).strip()
    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Invalid book information"}), 400
    return jsonify({"status": "Book added", "title": title, "author": author, "isbn": isbn}), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    section = section.strip()
    if not section:
        return jsonify({"status": "Error", "message": "Missing 'section' parameter"}), 400
    if not SECTION_PATTERN.fullmatch(section):
        return jsonify({"status": "Error", "message": "Invalid section name"}), 400
    try:
        subprocess.run(["python", "inventory_script.py", section], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception as e:
        return jsonify({"status": "Error", "message": f"Failed to start inventory: {str(e)}"}), 500
    return jsonify({"status": "Inventory check initiated"}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if not password:
        return jsonify({"status": "Access denied"}), 401
    if check_password_hash(LIBRARIAN_PASSWORD_HASH, password):
        return jsonify({"status": "Librarian access granted"}), 200
    else:
        return jsonify({"status": "Access denied"}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)