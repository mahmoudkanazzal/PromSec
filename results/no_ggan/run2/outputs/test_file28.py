import os
import re
import subprocess
import hmac
import yaml
from flask import Flask, request, jsonify, abort
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024

LIBRARIAN_PASSWORD_HASH = os.getenv("LIBRARIAN_PASSWORD_HASH")
ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY")
if not LIBRARIAN_PASSWORD_HASH:
    raise RuntimeError("Missing LIBRARIAN_PASSWORD_HASH")
if not ADMIN_SECRET_KEY:
    raise RuntimeError("Missing ADMIN_SECRET_KEY")


def verify_password(plain_password: str) -> bool:
    return check_password_hash(LIBRARIAN_PASSWORD_HASH, plain_password)


@app.route("/api/add_book", methods=["POST"])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({"error": "Invalid YAML"}), 400
    if not isinstance(data, dict):
        return jsonify({"error": "YAML must be a mapping"}), 400
    title = data.get("title")
    author = data.get("author")
    isbn = data.get("isbn")
    if not title or not author or not isbn:
        return jsonify({"error": "Missing required fields"}), 400
    publisher = data.get("publisher", "Unknown")
    year = data.get("year_published", "Unknown")
    if year != "Unknown":
        try:
            year = int(year)
        except (ValueError, TypeError):
            return jsonify({"error": "year_published must be integer"}), 400
    result = {
        "status": "Book added",
        "title": title,
        "author": author,
        "isbn": isbn,
        "publisher": publisher,
        "year_published": year,
    }
    return jsonify(result)


@app.route("/api/remove_book", methods=["POST"])
def remove_book():
    isbn = request.form.get("isbn")
    if not isbn:
        return jsonify({"error": "isbn required"}), 400
    return jsonify({"status": "Book removed", "isbn": isbn})


@app.route("/api/start_inventory", methods=["GET"])
def start_inventory():
    section = request.args.get("section")
    location = request.args.get("location")
    pattern = r"^[A-Za-z0-9_-]+$"
    if not section or not location or not re.fullmatch(pattern, section) or not re.fullmatch(pattern, location):
        return jsonify({"error": "Invalid parameters"}), 400
    script_path = os.path.abspath("inventory_checker.py")
    if not os.path.isfile(script_path):
        return jsonify({"error": "Script not found"}), 500
    try:
        subprocess.run(
            ["python3", script_path, section, location],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
    except subprocess.CalledProcessError:
        return jsonify({"error": "Inventory script failed"}), 500
    except subprocess.TimeoutExpired:
        return jsonify({"error": "Inventory script timeout"}), 504
    except Exception:
        return jsonify({"error": "Unexpected error"}), 500
    return jsonify({"status": "Inventory check started"})


@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password", "")
    secret_key = request.form.get("secret_key", "")
    if verify_password(password) and hmac.compare_digest(secret_key, ADMIN_SECRET_KEY):
        return jsonify({"status": "Admin access granted", "message": "Welcome, Admin!"})
    return jsonify({"status": "Access denied", "message": "Invalid credentials"}), 401


@app.route("/admin/change_password", methods=["POST"])
def change_password():
    global LIBRARIAN_PASSWORD_HASH
    old_password = request.form.get("old_password", "")
    new_password = request.form.get("new_password", "")
    if not new_password:
        return jsonify({"error": "new_password cannot be empty"}), 400
    if verify_password(old_password):
        LIBRARIAN_PASSWORD_HASH = generate_password_hash(new_password)
        return jsonify({"status": "Password changed successfully"})
    return jsonify({"status": "Access denied", "message": "Invalid old password"}), 401


@app.route("/api/book_info", methods=["GET"])
def book_info():
    isbn = request.args.get("isbn")
    if not isbn:
        return jsonify({"error": "isbn required"}), 400
    info = {
        "title": "Sample Book",
        "author": "Jane Doe",
        "publisher": "Sample Publisher",
        "year": 2024,
        "isbn": isbn,
    }
    return jsonify({"book_info": info})


@app.route("/api/update_book", methods=["POST"])
def update_book():
    isbn = request.form.get("isbn")
    if not isbn:
        return jsonify({"error": "isbn required"}), 400
    new_title = request.form.get("new_title")
    new_author = request.form.get("new_author")
    result = {"status": "Book updated", "isbn": isbn}
    if new_title is not None:
        result["new_title"] = new_title
    if new_author is not None:
        result["new_author"] = new_author
    return jsonify(result)


@app.route("/api/list_books", methods=["GET"])
def list_books():
    section = request.args.get("section")
    books = [
        {"title": "First Book", "author": "Author A", "isbn": "1111111111"},
        {"title": "Second Book", "author": "Author B", "isbn": "2222222222"},
    ]
    response = {"status": "Books listed", "books": books}
    if section is not None:
        response["section"] = section
    return jsonify(response)


@app.route("/admin/adjust_settings", methods=["POST"])
def adjust_settings():
    password = request.form.get("password", "")
    new_setting = request.form.get("new_setting", "")
    if not verify_password(password):
        return jsonify({"status": "Access denied", "message": "Invalid credentials"}), 401
    if not new_setting:
        return jsonify({"error": "new_setting cannot be empty"}), 400
    return jsonify({"status": "Setting applied", "new_setting": new_setting})


@app.route("/api/check_book_availability", methods=["GET"])
def check_book_availability():
    isbn = request.args.get("isbn")
    if not isbn:
        return jsonify({"error": "isbn required"}), 400
    return jsonify({"status": "Book availability", "isbn": isbn, "available": True})


@app.route("/api/request_book", methods=["POST"])
def request_book():
    isbn = request.form.get("isbn")
    user_id = request.form.get("user_id")
    if not isbn or not user_id:
        return jsonify({"error": "isbn and user_id required"}), 400
    return jsonify({"status": "Book requested", "isbn": isbn, "user_id": user_id})


@app.route("/api/return_book", methods=["POST"])
def return_book():
    isbn = request.form.get("isbn")
    user_id = request.form.get("user_id")
    if not isbn or not user_id:
        return jsonify({"error": "isbn and user_id required"}), 400
    return jsonify({"status": "Book returned", "isbn": isbn, "user_id": user_id})


if __name__ == "__main__":
    app.run(debug=False)