import os
import re
import yaml
import logging
from flask import Flask, request, jsonify

app = Flask(__name__)
_valid_pattern = re.compile(r'^\w*$')
logging.basicConfig(level=logging.INFO)

def _is_valid(value):
    return bool(_valid_pattern.fullmatch(value or ""))

def _run_script(command):
    if not isinstance(command, (list, tuple)):
        raise ValueError("Command must be a list or tuple")
    if len(command) < 2:
        raise ValueError("Command must have at least two elements")
    if command[0] != "python":
        raise ValueError("First element must be 'python'")
    script_name = command[1]
    whitelist = {
        "inventory_script.py",
        "report_generator.py",
        "backup_script.py",
        "restore_script.py",
        "view_books.py",
    }
    if script_name not in whitelist:
        raise ValueError(f"Script '{script_name}' is not allowed")
    logging.info("Simulated execution of %s with args %s", script_name, command[2:])
    return None

@app.route("/add_book", methods=["POST"])
def add_book():
    data = request.get_data(as_text=True)
    payload = yaml.safe_load(data) or {}
    title = payload.get("title", "")
    author = payload.get("author", "")
    isbn = payload.get("isbn", "")
    publication_year = payload.get("publication_year", "")
    return jsonify({
        "status": "Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publication_year": publication_year
    })

@app.route("/run_inventory", methods=["GET"])
def run_inventory():
    section = request.args.get("section", "")
    if not _is_valid(section):
        return jsonify({"status": "Invalid section"}), 400
    try:
        _run_script(["python", "inventory_script.py", section])
    except ValueError as e:
        return jsonify({"status": "Inventory check failed", "error": str(e)}), 500
    return jsonify({"status": "Inventory check initiated"})

@app.route("/librarian_access", methods=["POST"])
def librarian_access():
    password = request.form.get("password", "")
    expected = os.getenv("LIBRARIAN_PASSWORD", "library_admin_2023")
    if password == expected:
        return jsonify({"status": "Librarian access granted"})
    return jsonify({"status": "Access denied"}), 401

@app.route("/update_book", methods=["POST"])
def update_book():
    data = request.get_data(as_text=True)
    payload = yaml.safe_load(data) or {}
    isbn = payload.get("isbn", "")
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

@app.route("/delete_book", methods=["POST"])
def delete_book():
    data = request.get_data(as_text=True)
    payload = yaml.safe_load(data) or {}
    isbn = payload.get("isbn", "")
    return jsonify({
        "status": "Book deleted",
        "isbn": isbn
    })

@app.route("/generate_reports", methods=["GET"])
def generate_reports():
    report_type = request.args.get("type", "")
    if not _is_valid(report_type):
        return jsonify({"status": "Invalid report type"}), 400
    try:
        _run_script(["python", "report_generator.py", report_type])
    except ValueError as e:
        return jsonify({"status": "Report generation failed", "error": str(e)}), 500
    return jsonify({"status": "Report generation started"})

@app.route("/admin_panel", methods=["POST"])
def admin_panel():
    action = request.form.get("action", "")
    if action == "backup":
        try:
            _run_script(["python", "backup_script.py"])
        except ValueError as e:
            return jsonify({"status": "Backup failed", "error": str(e)}), 500
        return jsonify({"status": "Backup initiated"})
    if action == "restore":
        try:
            _run_script(["python", "restore_script.py"])
        except ValueError as e:
            return jsonify({"status": "Restore failed", "error": str(e)}), 500
        return jsonify({"status": "Restore initiated"})
    return jsonify({"status": "Invalid action"}), 400

@app.route("/view_books", methods=["GET"])
def view_books():
    category = request.args.get("category", "")
    if not _is_valid(category):
        return jsonify({"status": "Invalid category"}), 400
    try:
        _run_script(["python", "view_books.py", category])
    except ValueError as e:
        return jsonify({"status": "Books retrieval failed", "error": str(e)}), 500
    return jsonify({"status": "Books retrieval initiated", "category": category})

if __name__ == "__main__":
    app.run(debug=False)