import os
import mimetypes
import yaml
from flask import Flask, request, jsonify

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if LIBRARIAN_PASSWORD is None:
    raise RuntimeError("LIBRARIAN_PASSWORD not set")

app = Flask(__name__)

SECTION_WHITELIST = ["fiction", "nonfiction", "reference", "children"]
REPORT_TYPE_WHITELIST = ["daily", "weekly", "monthly"]
CATEGORY_WHITELIST = ["science", "arts", "history", "technology"]
ADMIN_ACTIONS = {"backup": "backup_script.py", "restore": "restore_script.py"}

def parse_yaml(data):
    try:
        obj = yaml.safe_load(data)
        if isinstance(obj, dict):
            return obj
        return None
    except Exception:
        return None

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        raw = request.get_data(as_text=True)
        data = parse_yaml(raw)
        if not data or not all(k in data for k in ("title", "author", "isbn")):
            return jsonify({"error": "Invalid input"}), 400
        return jsonify({"status": "Book added", "title": data["title"], "author": data["author"], "isbn": data["isbn"]}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    try:
        section = request.args.get('section')
        if section not in SECTION_WHITELIST:
            return jsonify({"error": "Invalid section"}), 400
        mimetypes.guess_type(section)
        return jsonify({"status": "Inventory check initiated"}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    try:
        password = request.form.get('password')
        if password == LIBRARIAN_PASSWORD:
            return jsonify({"status": "Librarian access granted"}), 200
        return jsonify({"error": "Access denied"}), 401
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/update_book', methods=['POST'])
def update_book():
    try:
        raw = request.get_data(as_text=True)
        data = parse_yaml(raw)
        if not data or "isbn" not in data:
            return jsonify({"error": "Invalid input"}), 400
        response = {"status": "Book updated", "isbn": data["isbn"]}
        for key in ("new_title", "new_author", "new_year"):
            if key in data:
                response[key] = data[key]
        return jsonify(response), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        raw = request.get_data(as_text=True)
        data = parse_yaml(raw)
        if not data or "isbn" not in data:
            return jsonify({"error": "Invalid input"}), 400
        return jsonify({"status": "Book deleted", "isbn": data["isbn"]}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    try:
        rtype = request.args.get('type')
        if rtype not in REPORT_TYPE_WHITELIST:
            return jsonify({"error": "Invalid report type"}), 400
        mimetypes.guess_type(rtype)
        return jsonify({"status": "Report generation started"}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    try:
        action = request.form.get('action')
        script = ADMIN_ACTIONS.get(action)
        if not script:
            return jsonify({"error": "Invalid action"}), 400
        mimetypes.guess_type(script)
        if action == "backup":
            return jsonify({"status": "Backup initiated"}), 200
        return jsonify({"status": "Restore initiated"}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/view_books', methods=['GET'])
def view_books():
    try:
        category = request.args.get('category')
        if category not in CATEGORY_WHITELIST:
            return jsonify({"error": "Invalid category"}), 400
        mimetypes.guess_type(category)
        return jsonify({"status": "Books retrieval initiated", "category": category}), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/add_member', methods=['POST'])
def add_member():
    try:
        raw = request.get_data(as_text=True)
        data = parse_yaml(raw)
        if not data or not all(k in data for k in ("name", "id")):
            return jsonify({"error": "Invalid input"}), 400
        response = {"status": "Member added", "name": data["name"], "id": data["id"]}
        if "membership_date" in data:
            response["membership_date"] = data["membership_date"]
        return jsonify(response), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

@app.route('/update_member', methods=['POST'])
def update_member():
    try:
        raw = request.get_data(as_text=True)
        data = parse_yaml(raw)
        if not data or "id" not in data:
            return jsonify({"error": "Invalid input"}), 400
        response = {"status": "Member updated", "id": data["id"]}
        if "new_name" in data:
            response["new_name"] = data["new_name"]
        if "new_date" in data:
            response["new_date"] = data["new_date"]
        return jsonify(response), 200
    except Exception:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=False)