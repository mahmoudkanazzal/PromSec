import os
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'library_admin_2023')
ALLOWED_SECTIONS = ["fiction", "nonfiction", "reference", "children"]
ALLOWED_REPORT_TYPES = ["summary", "detailed", "statistics"]
ALLOWED_CATEGORIES = ["science", "arts", "history", "technology"]
ALLOWED_ADMIN_ACTIONS = {"backup": ["python", "backup_script.py"], "restore": ["python", "restore_script.py"]}

def error_response(message, status_code):
    return jsonify(message), status_code

def validate_required(data, fields):
    for field in fields:
        if field not in data or not data[field]:
            return False, f"Missing or empty required field: {field}"
    return True, None

def run_inventory_section(section):
    return True

def run_report(rtype):
    return True

def run_view_books(category):
    return True

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        payload = yaml.safe_load(request.data)
    except Exception:
        return error_response({"error": "Invalid YAML"}, 400)
    if not isinstance(payload, dict):
        return error_response({"error": "Invalid payload format"}, 400)
    ok, msg = validate_required(payload, ["title", "author", "isbn"])
    if not ok:
        return error_response({"error": msg}, 400)
    response = {
        "status": "Book added",
        "title": payload["title"],
        "author": payload["author"],
        "isbn": payload["isbn"]
    }
    if "publication_year" in payload:
        response["publication_year"] = payload["publication_year"]
    return jsonify(response)

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    if not section or section not in ALLOWED_SECTIONS:
        return error_response({"error": "Invalid or missing section"}, 400)
    run_inventory_section(section)
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
        payload = yaml.safe_load(request.data)
    except Exception:
        return error_response({"error": "Invalid YAML"}, 400)
    if not isinstance(payload, dict):
        return error_response({"error": "Invalid payload format"}, 400)
    ok, msg = validate_required(payload, ["isbn"])
    if not ok:
        return error_response({"error": msg}, 400)
    response = {
        "status": "Book updated",
        "isbn": payload["isbn"]
    }
    if "title" in payload:
        response["new_title"] = payload["title"]
    if "author" in payload:
        response["new_author"] = payload["author"]
    if "publication_year" in payload:
        response["new_year"] = payload["publication_year"]
    return jsonify(response)

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        payload = yaml.safe_load(request.data)
    except Exception:
        return error_response({"error": "Invalid YAML"}, 400)
    if not isinstance(payload, dict):
        return error_response({"error": "Invalid payload format"}, 400)
    ok, msg = validate_required(payload, ["isbn"])
    if not ok:
        return error_response({"error": msg}, 400)
    return jsonify({"status": "Book deleted", "isbn": payload["isbn"]})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    rtype = request.args.get('type')
    if not rtype or rtype not in ALLOWED_REPORT_TYPES:
        return error_response({"error": "Invalid or missing report type"}, 400)
    run_report(rtype)
    return jsonify({"status": "Report generation started"})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action')
    if action not in ALLOWED_ADMIN_ACTIONS:
        return error_response({"error": "Invalid admin action"}, 400)
    status_msg = "Backup initiated" if action == "backup" else "Restore initiated"
    return jsonify({"status": status_msg})

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category')
    if not category or category not in ALLOWED_CATEGORIES:
        return error_response({"error": "Invalid or missing category"}, 400)
    run_view_books(category)
    return jsonify({"status": "Books retrieval initiated", "category": category})

@app.route('/add_member', methods=['POST'])
def add_member():
    try:
        payload = yaml.safe_load(request.data)
    except Exception:
        return error_response({"error": "Invalid YAML"}, 400)
    if not isinstance(payload, dict):
        return error_response({"error": "Invalid payload format"}, 400)
    ok, msg = validate_required(payload, ["name", "id"])
    if not ok:
        return error_response({"error": msg}, 400)
    response = {
        "status": "Member added",
        "name": payload["name"],
        "id": payload["id"],
        "membership_date": "2023-01-01"
    }
    return jsonify(response)

@app.route('/update_member', methods=['POST'])
def update_member():
    try:
        payload = yaml.safe_load(request.data)
    except Exception:
        return error_response({"error": "Invalid YAML"}, 400)
    if not isinstance(payload, dict):
        return error_response({"error": "Invalid payload format"}, 400)
    ok, msg = validate_required(payload, ["id"])
    if not ok:
        return error_response({"error": msg}, 400)
    response = {
        "status": "Member updated",
        "id": payload["id"]
    }
    if "name" in payload:
        response["new_name"] = payload["name"]
    if "membership_date" in payload:
        response["new_date"] = payload["membership_date"]
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)