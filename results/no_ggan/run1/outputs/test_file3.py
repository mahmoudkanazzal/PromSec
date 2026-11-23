import os
import yaml
import subprocess
import hmac
from flask import Flask, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

LIBRARIAN_PASSWORD_HASH = os.getenv("LIBRARIAN_PASSWORD_HASH")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")
if not LIBRARIAN_PASSWORD_HASH:
    raise RuntimeError("Missing LIBRARIAN_PASSWORD_HASH environment variable")
if not ADMIN_SECRET_KEY:
    raise RuntimeError("Missing ADMIN_SECRET_KEY environment variable")

def is_safe_path_component(value: str) -> bool:
    return all(c.isalnum() or c in "-_" for c in value)

@app.route("/library/add_book", methods=["POST"])
def add_book():
    try:
        raw = request.get_data(as_text=True)
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    title = data.get("title")
    author = data.get("author")
    isbn = data.get("isbn")
    publisher = data.get("publisher", "Unknown")
    year_published = data.get("year_published", "Unknown")
    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Missing required fields"}), 400
    if year_published != "Unknown" and not isinstance(year_published, int):
        return jsonify({"status": "Error", "message": "year_published must be an integer"}), 400
    response = {
        "status": "Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publisher": publisher,
        "year_published": year_published,
    }
    return jsonify(response)

@app.route("/library/remove_book", methods=["POST"])
def remove_book():
    isbn = request.form.get("isbn")
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN missing"}), 400
    return jsonify({"status": "Book removed", "isbn": isbn})

@app.route("/inventory/check", methods=["GET"])
def inventory_check():
    section = request.args.get("section")
    location = request.args.get("location")
    if not section or not location:
        return jsonify({"status": "Error", "message": "Missing parameters"}), 400
    if not is_safe_path_component(section) or not is_safe_path_component(location):
        return jsonify({"status": "Error", "message": "Invalid path components"}), 400
    try:
        subprocess.run(
            ["python3", "inventory_check.py", section, location],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        return jsonify({"status": "Error", "message": "Subprocess execution failed"}), 500
    return jsonify({"status": "Inventory check started"})

@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password")
    secret_key = request.form.get("secret_key")
    if not password or not secret_key:
        return jsonify({"status": "Access denied", "message": "Invalid credentials"}), 401
    pwd_ok = check_password_hash(LIBRARIAN_PASSWORD_HASH, password)
    key_ok = hmac.compare_digest(secret_key, ADMIN_SECRET_KEY)
    if pwd_ok and key_ok:
        return jsonify({"status": "Admin access granted", "message": "Welcome, Admin!"})
    return jsonify({"status": "Access denied", "message": "Invalid credentials"}), 401

@app.route("/admin/change_password", methods=["POST"])
def change_password():
    global LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    if not new_password:
        return jsonify({"status": "Error", "message": "New password cannot be empty"}), 400
    if old_password and check_password_hash(LIBRARIAN_PASSWORD_HASH, old_password):
        LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)
        return jsonify({"status": "Password changed successfully"})
    return jsonify({"status": "Error", "message": "Invalid old password"}), 401

@app.route("/library/book_info", methods=["GET"])
def book_info():
    isbn = request.args.get("isbn")
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN missing"}), 400
    info = {
        "isbn": isbn,
        "title": "Sample Title",
        "author": "Sample Author",
        "publisher": "Sample Publisher",
        "year_published": "Unknown",
    }
    return jsonify(info)

@app.route("/library/update_book", methods=["POST"])
def update_book():
    isbn = request.form.get("isbn")
    new_title = request.form.get("new_title")
    new_author = request.form.get("new_author")
    if not isbn:
        return jsonify({"status": "Error", "message": "ISBN missing"}), 400
    return jsonify({
        "status": "Book updated",
        "isbn": isbn,
        "new_title": new_title,
        "new_author": new_author,
    })

@app.route("/library/list_books", methods=["GET"])
def list_books():
    section = request.args.get("section")
    books = [
        {"title": "Book One", "author": "Author A", "isbn": "111"},
        {"title": "Book Two", "author": "Author B", "isbn": "222"},
    ]
    return jsonify({
        "status": "Books listed",
        "section": section,
        "books": books,
    })

if __name__ == "__main__":
    app.run(debug=False)