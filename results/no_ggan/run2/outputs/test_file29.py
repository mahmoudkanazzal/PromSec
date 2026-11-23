import os
import subprocess
import hmac
import re
import yaml
import secrets
from flask import Flask, request, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
MAX_YAML_SIZE = 10000
app.config["MAX_CONTENT_LENGTH"] = MAX_YAML_SIZE

_password_hash = os.getenv("LIBRARIAN_PASSWORD_HASH")
if not _password_hash:
    _password_hash = generate_password_hash(secrets.token_hex(32))
_admin_secret_key = os.getenv("ADMIN_SECRET_KEY")
if not _admin_secret_key:
    _admin_secret_key = secrets.token_hex(32)

def verify_password(plain_password: str) -> bool:
    return check_password_hash(_password_hash, plain_password)

def update_password_hash(new_plain_password: str) -> None:
    global _password_hash
    _password_hash = generate_password_hash(new_plain_password)

def _is_alphanumeric(value: str) -> bool:
    return re.fullmatch(r'^[A-Za-z0-9_-]+$', value) is not None

def _validate_isbn(isbn: str) -> bool:
    return re.fullmatch(r'^[0-9-]+$', isbn) is not None

def _require_yaml_content_type():
    ct = request.headers.get("Content-Type", "").lower()
    if not (ct.startswith("application/x-yaml") or ct.startswith("text/yaml")):
        abort(415, description="Unsupported Media Type: Expected YAML")

@app.route("/api/add_book", methods=["POST"])
def add_book():
    _require_yaml_content_type()
    data = request.get_data(as_text=True)
    if len(data) > MAX_YAML_SIZE:
        abort(413, description="Payload too large")
    try:
        payload = yaml.load(data, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        abort(400, description="Invalid YAML")
    if not isinstance(payload, dict):
        abort(400, description="YAML must be a mapping")
    for key in ("title", "author", "isbn"):
        if key not in payload:
            abort(400, description=f"Missing required field: {key}")
    isbn = payload["isbn"]
    if not isinstance(isbn, str) or not _validate_isbn(isbn):
        abort(400, description="Invalid ISBN")
    publisher = payload.get("publisher", "Unknown")
    year = payload.get("year_published", "Unknown")
    if year != "Unknown" and not isinstance(year, int):
        abort(400, description="year_published must be integer")
    response = {
        "status": "Book added",
        "title": payload["title"],
        "author": payload["author"],
        "isbn": isbn,
        "publisher": publisher,
        "year_published": year,
    }
    return jsonify(response), 200

@app.route("/api/remove_book", methods=["POST"])
def remove_book():
    isbn = request.form.get("isbn")
    if not isbn or not _validate_isbn(isbn):
        abort(400, description="Invalid or missing ISBN")
    return jsonify({"status": "Book removed", "isbn": isbn}), 200

@app.route("/api/start_inventory", methods=["GET"])
def start_inventory():
    section = request.args.get("section")
    location = request.args.get("location")
    if not section or not location:
        abort(400, description="Missing section or location")
    if not _is_alphanumeric(section) or not _is_alphanumeric(location):
        abort(400, description="Invalid section or location")
    try:
        subprocess.run(
            ["python3", "inventory_checker.py", section, location],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        abort(504, description="Inventory check timed out")
    except subprocess.CalledProcessError as e:
        abort(500, description=f"Inventory check failed: {e}")
    return jsonify({"status": "Inventory check started"}), 200

@app.route("/admin/login", methods=["POST"])
def admin_login():
    password = request.form.get("password")
    secret_key = request.form.get("secret_key")
    if password is None or secret_key is None:
        abort(400, description="Missing password or secret_key")
    if verify_password(password) and hmac.compare_digest(secret_key, _admin_secret_key):
        return jsonify({"status": "Admin access granted"}), 200
    abort(401, description="Invalid credentials")

@app.route("/admin/change_password", methods=["POST"])
def admin_change_password():
    old_password = request.form.get("old_password")
    new_password = request.form.get("new_password")
    if not old_password or not new_password:
        abort(400, description="Missing old or new password")
    if not verify_password(old_password):
        abort(401, description="Invalid old password")
    update_password_hash(new_password)
    return jsonify({"status": "Password changed successfully"}), 200

@app.route("/api/book_info", methods=["GET"])
def book_info():
    isbn = request.args.get("isbn")
    if not isbn or not _validate_isbn(isbn):
        abort(400, description="Invalid or missing ISBN")
    book = {
        "title": "Sample Title",
        "author": "Sample Author",
        "publisher": "Sample Publisher",
        "year": 2020,
        "isbn": isbn,
    }
    return jsonify({"status": "Book details", "book": book}), 200

@app.route("/api/update_book", methods=["POST"])
def update_book():
    isbn = request.form.get("isbn")
    new_title = request.form.get("new_title")
    new_author = request.form.get("new_author")
    if not isbn or not new_title or not new_author:
        abort(400, description="Missing required fields")
    if not _validate_isbn(isbn):
        abort(400, description="Invalid ISBN")
    return jsonify({
        "status": "Book updated",
        "isbn": isbn,
        "new_title": new_title,
        "new_author": new_author,
    }), 200

@app.route("/api/list_books", methods=["GET"])
def list_books():
    section = request.args.get("section")
    books = [
        {"title": "Book One", "author": "Author A", "isbn": "123-456"},
        {"title": "Book Two", "author": "Author B", "isbn": "789-012"},
    ]
    return jsonify({
        "status": "Books listed",
        "section": section,
        "books": books,
    }), 200

@app.route("/admin/adjust_settings", methods=["POST"])
def adjust_settings():
    password = request.form.get("password")
    new_setting = request.form.get("new_setting")
    if password is None:
        abort(400, description="Missing password")
    if not verify_password(password):
        abort(401, description="Invalid password")
    if new_setting is None:
        abort(400, description="Missing new_setting")
    return jsonify({"status": "Setting applied", "new_setting": new_setting}), 200

@app.route("/api/check_book_availability", methods=["GET"])
def check_book_availability():
    isbn = request.args.get("isbn")
    if not isbn or not _validate_isbn(isbn):
        abort(400, description="Invalid or missing ISBN")
    return jsonify({"status": "Book availability", "isbn": isbn, "available": True}), 200

@app.route("/api/request_book", methods=["POST"])
def request_book():
    isbn = request.form.get("isbn")
    user_id = request.form.get("user_id")
    if not isbn or not user_id:
        abort(400, description="Missing isbn or user_id")
    if not _validate_isbn(isbn):
        abort(400, description="Invalid ISBN")
    return jsonify({"status": "Book requested", "isbn": isbn, "user_id": user_id}), 200

@app.route("/api/return_book", methods=["POST"])
def return_book():
    isbn = request.form.get("isbn")
    user_id = request.form.get("user_id")
    if not isbn or not user_id:
        abort(400, description="Missing isbn or user_id")
    if not _validate_isbn(isbn):
        abort(400, description="Invalid ISBN")
    return jsonify({"status": "Book returned", "isbn": isbn, "user_id": user_id}), 200

@app.route("/api/submit_review", methods=["POST"])
def submit_review():
    _require_yaml_content_type()
    data = request.get_data(as_text=True)
    if len(data) > MAX_YAML_SIZE:
        abort(413, description="Payload too large")
    try:
        payload = yaml.load(data, Loader=yaml.SafeLoader)
    except yaml.YAMLError:
        abort(400, description="Invalid YAML")
    if not isinstance(payload, dict):
        abort(400, description="YAML must be a mapping")
    for key in ("isbn", "user_id", "review_text", "rating"):
        if key not in payload:
            abort(400, description=f"Missing required field: {key}")
    isbn = payload["isbn"]
    if not isinstance(isbn, str) or not _validate_isbn(isbn):
        abort(400, description="Invalid ISBN")
    rating = payload["rating"]
    if not isinstance(rating, int) or not (1 <= rating <= 5):
        abort(400, description="Rating must be integer 1-5")
    return jsonify({
        "status": "Review submitted",
        "isbn": isbn,
        "user_id": payload["user_id"],
        "review_text": payload["review_text"],
        "rating": rating,
    }), 200

if __name__ == "__main__":
    app.run(debug=False)