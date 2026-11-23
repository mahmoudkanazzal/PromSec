import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_this_password!')

SAFE_ARG_PATTERN = re.compile(r'^[a-zA-Z0-9_\-]+$')

def is_safe_argument(arg: str) -> bool:
    return bool(SAFE_ARG_PATTERN.fullmatch(arg))

def run_script(script_name: str, *args):
    for arg in args:
        if not is_safe_argument(str(arg)):
            raise ValueError(f"Unsafe argument: {arg}")
    cmd = ["python", script_name] + list(args)
    subprocess.run(cmd, check=False)

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
        if not isinstance(payload, dict):
            raise ValueError
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    required = ['title', 'author', 'isbn']
    missing = [k for k in required if k not in payload]
    if missing:
        return jsonify(error=f"Missing fields: {', '.join(missing)}"), 400
    response = {
        "status": "Book added",
        "title": payload['title'],
        "author": payload['author'],
        "isbn": payload['isbn']
    }
    return jsonify(response)

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not is_safe_argument(section):
        return jsonify(error="Invalid section parameter"), 400
    try:
        run_script("inventory_script.py", section)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(status="Inventory check initiated")

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify(status="Librarian access granted")
    return jsonify(status="Access denied"), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
        if not isinstance(payload, dict):
            raise ValueError
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    if 'isbn' not in payload:
        return jsonify(error="Missing field: isbn"), 400
    response = {"status": "Book updated", "isbn": payload['isbn']}
    for field in ['new_title', 'new_author', 'new_year']:
        if field in payload:
            response[field] = payload[field]
    return jsonify(response)

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
        if not isinstance(payload, dict):
            raise ValueError
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    if 'isbn' not in payload:
        return jsonify(error="Missing field: isbn"), 400
    return jsonify(status="Book deleted", isbn=payload['isbn'])

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if not is_safe_argument(report_type):
        return jsonify(error="Invalid type parameter"), 400
    try:
        run_script("report_generator.py", report_type)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(status="Report generation started")

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == "backup":
        try:
            run_script("backup_script.py")
        except Exception as e:
            return jsonify(error=str(e)), 500
        return jsonify(status="Backup initiated")
    if action == "restore":
        try:
            run_script("restore_script.py")
        except Exception as e:
            return jsonify(error=str(e)), 500
        return jsonify(status="Restore initiated")
    return jsonify(error="Invalid action"), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not is_safe_argument(category):
        return jsonify(error="Invalid category parameter"), 400
    try:
        run_script("view_books.py", category)
    except Exception as e:
        return jsonify(error=str(e)), 500
    return jsonify(status="Books retrieval initiated", category=category)

@app.route('/add_member', methods=['POST'])
def add_member():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
        if not isinstance(payload, dict):
            raise ValueError
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    required = ['name', 'id']
    missing = [k for k in required if k not in payload]
    if missing:
        return jsonify(error=f"Missing fields: {', '.join(missing)}"), 400
    response = {
        "status": "Member added",
        "name": payload['name'],
        "id": payload['id']
    }
    if 'membership_date' in payload:
        response['membership_date'] = payload['membership_date']
    return jsonify(response)

@app.route('/update_member', methods=['POST'])
def update_member():
    try:
        data = request.get_data(as_text=True)
        payload = yaml.safe_load(data)
        if not isinstance(payload, dict):
            raise ValueError
    except Exception:
        return jsonify(error="Invalid YAML"), 400
    if 'id' not in payload:
        return jsonify(error="Missing field: id"), 400
    response = {"status": "Member updated", "id": payload['id']}
    for field in ['new_name', 'new_date']:
        if field in payload:
            response[field] = payload[field]
    return jsonify(response)

if __name__ == "__main__":
    app.run(debug=False)