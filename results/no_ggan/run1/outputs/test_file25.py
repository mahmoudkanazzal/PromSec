import os
import subprocess
import re
from flask import Flask, request, jsonify
import yaml
from typing import Tuple

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if not LIBRARIAN_PASSWORD:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD must be set")

SAFE_ARG_RE = re.compile(r"^[\w\-]+$")

def _run_script(script_name: str, arg: str = "") -> Tuple[bool, str]:
    try:
        if arg and not SAFE_ARG_RE.fullmatch(arg):
            return False, f"Invalid argument: {arg}"
        cmd = ["python", script_name]
        if arg:
            cmd.append(arg)
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            err = result.stderr.strip() or "Script execution failed"
            return False, err
        return True, result.stdout.strip()
    except Exception as e:
        return False, str(e)

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    title = data.get('title', '') if isinstance(data, dict) else ''
    author = data.get('author', '') if isinstance(data, dict) else ''
    isbn = data.get('isbn', '') if isinstance(data, dict) else ''
    publication_year = data.get('publication_year', '') if isinstance(data, dict) else ''
    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Invalid book information"}), 400
    return jsonify({
        "status": "Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publication_year": publication_year
    }), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    success, msg = _run_script("inventory_script.py", section)
    if not success:
        return jsonify({"status": "Error", "message": msg}), 400
    return jsonify({"status": "Inventory check initiated"}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({"status": "Librarian access granted"}), 200
    return jsonify({"status": "Access denied"}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    isbn = data.get('isbn', '') if isinstance(data, dict) else ''
    new_title = data.get('new_title', '') if isinstance(data, dict) else ''
    new_author = data.get('new_author', '') if isinstance(data, dict) else ''
    new_year = data.get('new_year', '') if isinstance(data, dict) else ''
    if not isbn:
        return jsonify({"status": "Error", "message": "Invalid book information"}), 400
    return jsonify({
        "status": "Book updated",
        "isbn": isbn,
        "new_title": new_title,
        "new_author": new_author,
        "new_year": new_year
    }), 200

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    isbn = data.get('isbn', '') if isinstance(data, dict) else ''
    if not isbn:
        return jsonify({"status": "Error", "message": "Invalid book information"}), 400
    return jsonify({"status": "Book deleted", "isbn": isbn}), 200

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    success, msg = _run_script("report_generator.py", report_type)
    if not success:
        return jsonify({"status": "Error", "message": msg}), 400
    return jsonify({"status": "Report generation started"}), 200

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == "backup":
        success, msg = _run_script("backup_script.py")
        if not success:
            return jsonify({"status": "Error", "message": msg}), 500
        return jsonify({"status": "Backup initiated"}), 200
    if action == "restore":
        success, msg = _run_script("restore_script.py")
        if not success:
            return jsonify({"status": "Error", "message": msg}), 500
        return jsonify({"status": "Restore initiated"}), 200
    return jsonify({"status": "Invalid action"}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    success, msg = _run_script("view_books.py", category)
    if not success:
        return jsonify({"status": "Error", "message": msg}), 400
    return jsonify({"status": "Books retrieval initiated", "category": category}), 200

@app.route('/add_member', methods=['POST'])
def add_member():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    name = data.get('name', '') if isinstance(data, dict) else ''
    member_id = data.get('id', '') if isinstance(data, dict) else ''
    membership_date = data.get('membership_date', '') if isinstance(data, dict) else ''
    if not name or not member_id:
        return jsonify({"status": "Error", "message": "Invalid member information"}), 400
    return jsonify({
        "status": "Member added",
        "name": name,
        "id": member_id,
        "membership_date": membership_date
    }), 200

@app.route('/update_member', methods=['POST'])
def update_member():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    member_id = data.get('id', '') if isinstance(data, dict) else ''
    new_name = data.get('new_name', '') if isinstance(data, dict) else ''
    new_date = data.get('new_date', '') if isinstance(data, dict) else ''
    if not member_id:
        return jsonify({"status": "Error", "message": "Invalid member information"}), 400
    return jsonify({
        "status": "Member updated",
        "id": member_id,
        "new_name": new_name,
        "new_date": new_date
    }), 200

if __name__ == "__main__":
    app.run(debug=False)