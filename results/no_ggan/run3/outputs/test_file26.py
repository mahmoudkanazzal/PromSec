import os
import re
import yaml
import subprocess
import hmac
from flask import Flask, request, jsonify

app = Flask(__name__)

_LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if _LIBRARIAN_PASSWORD is None:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD must be set for admin access.")

_SECTION_REGEX = re.compile(r'^[A-Za-z0-9_-]+$')

def _validate_book_info(book_info):
    if not isinstance(book_info, dict):
        raise ValueError("Book information must be a dictionary")
    required_keys = ("title", "author", "isbn")
    for key in required_keys:
        if key not in book_info:
            raise ValueError(f"Missing required field: {key}")
        if not isinstance(book_info[key], str):
            raise ValueError(f"Field {key} must be a string")
        if not book_info[key].strip():
            raise ValueError(f"Field {key} cannot be empty")
    title = book_info["title"].strip()
    author = book_info["author"].strip()
    isbn = book_info["isbn"].strip()
    return title, author, isbn

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    try:
        title, author, isbn = _validate_book_info(data)
    except ValueError as e:
        return jsonify({"status": "Error", "message": str(e)}), 400
    return jsonify({"status": "New Book added", "title": title, "author": author, "isbn": isbn})

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '').strip()
    if section:
        if not _SECTION_REGEX.fullmatch(section):
            return jsonify({"status": "Error", "message": "Invalid section parameter"}), 400
    cmd = ["python3", "run_inventory.py"]
    if section:
        cmd.append(section)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return jsonify({"status": "Error", "message": "Inventory execution failed"}), 500
    return jsonify({"status": "Inventory check started"})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, _LIBRARIAN_PASSWORD):
        return jsonify({"status": "Admin access granted"})
    return jsonify({"status": "Access denied"}), 401

if __name__ == "__main__":
    app.run(debug=False)