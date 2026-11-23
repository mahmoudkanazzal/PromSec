import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if LIBRARIAN_PASSWORD is None:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD must be set")

ARG_PATTERN = re.compile(r'^[A-Za-z0-9_-]+$')

def _is_valid_arg(arg: str) -> bool:
    return bool(ARG_PATTERN.fullmatch(arg))

def _run_script(script_name: str, *args):
    cmd = ["python", script_name] + list(args)
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
    except yaml.YAMLError:
        return jsonify({"status": "Invalid YAML format"}), 400
    if not isinstance(payload, dict):
        return jsonify({"status": "Invalid YAML format"}), 400
    required = ["title", "author", "isbn", "publication_year"]
    if not all(k in payload for k in required):
        return jsonify({"status": "Missing required book fields"}), 400
    return jsonify({
        "status": "Book added",
        "title": payload["title"],
        "author": payload["author"],
        "isbn": payload["isbn"],
        "publication_year": payload["publication_year"]
    })

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    if section is not None:
        if not _is_valid_arg(section):
            return jsonify({"status": "Invalid section parameter"}), 400
        _run_script("inventory_script.py", section)
    else:
        _run_script("inventory_script.py")
    return jsonify({"status": "Inventory check initiated"})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({"status": "Librarian access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
    except yaml.YAMLError:
        return jsonify({"status": "Invalid YAML format"}), 400
    if not isinstance(payload, dict):
        return jsonify({"status": "Invalid YAML format"}), 400
    isbn = payload.get("isbn")
    if not isbn:
        return jsonify({"status": "Missing ISBN"}), 400
    new_title = payload.get("new_title", "")
    new_author = payload.get("new_author", "")
    new_year = payload.get("new_year", "")
    return jsonify({
        "status": "Book updated",
        "isbn": isbn,
        "new_title": new_title,
        "new_author": new_author,
        "new_year": new_year
    })

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
    except yaml.YAMLError:
        return jsonify({"status": "Invalid YAML format"}), 400
    if not isinstance(payload, dict):
        return jsonify({"status": "Invalid YAML format"}), 400
    isbn = payload.get("isbn")
    if not isbn:
        return jsonify({"status": "Missing ISBN"}), 400
    return jsonify({"status": "Book deleted", "isbn": isbn})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type')
    if report_type is not None:
        if not _is_valid_arg(report_type):
            return jsonify({"status": "Invalid report type"}), 400
        _run_script("report_generator.py", report_type)
    else:
        _run_script("report_generator.py")
    return jsonify({"status": "Report generation started"})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action')
    if action == "backup":
        _run_script("backup_script.py")
        return jsonify({"status": "Backup initiated"})
    if action == "restore":
        _run_script("restore_script.py")
        return jsonify({"status": "Restore initiated"})
    return jsonify({"status": "Invalid action"}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category')
    if category is not None:
        if not _is_valid_arg(category):
            return jsonify({"status": "Invalid category"}), 400
        _run_script("view_books.py", category)
    else:
        _run_script("view_books.py")
    return jsonify({"status": "Books retrieval initiated", "category": category})

if __name__ == "__main__":
    app.run(debug=False)