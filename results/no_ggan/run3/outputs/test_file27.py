import os
import re
import hmac
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)
ADMIN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
SAFE_ARG_PATTERN = re.compile(r"^[\w-]+$")

def is_safe_arg(value: str) -> bool:
    return bool(SAFE_ARG_PATTERN.fullmatch(value))

def run_script(script_path: str, *args):
    cmd = ["python3", script_path] + list(args)
    subprocess.run(cmd, check=False)

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    try:
        raw = request.get_data()
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    genre = data.get('genre')
    publication_year = data.get('publication_year')
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Missing required fields"}), 400
    return jsonify({
        "status":"New Book added",
        "title":title,
        "author":author,
        "isbn":isbn,
        "genre":genre,
        "publication_year":publication_year
    })

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not is_safe_arg(section):
        return jsonify({"status":"Error","message":"Invalid section"}), 400
    run_script("run_inventory.py", section)
    return jsonify({"status":"Inventory check started","section":section})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    if ADMIN_PASSWORD is None:
        return jsonify({"status":"Error","message":"Server misconfiguration"}), 500
    password = request.form.get('password', '')
    if hmac.compare_digest(password, ADMIN_PASSWORD):
        return jsonify({"status":"Admin access granted"})
    else:
        return jsonify({"status":"Access denied"}), 401

@app.route('/update_book_details', methods=['POST'])
def update_book_details():
    try:
        raw = request.get_data()
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    isbn = data.get('isbn')
    new_title = data.get('new_title')
    new_author = data.get('new_author')
    new_genre = data.get('new_genre')
    new_publication_year = data.get('new_publication_year')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN required"}), 400
    return jsonify({
        "status":"Book details updated",
        "isbn":isbn,
        "new_title":new_title,
        "new_author":new_author,
        "new_genre":new_genre,
        "new_publication_year":new_publication_year
    })

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        raw = request.get_data()
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    isbn = data.get('isbn')
    if not isbn:
        return jsonify({"status":"Error","message":"ISBN required"}), 400
    return jsonify({"status":"Book deleted","isbn":isbn})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if not is_safe_arg(report_type):
        return jsonify({"status":"Error","message":"Invalid type"}), 400
    run_script("report_generator.py", report_type)
    return jsonify({"status":"Report generation started","type":report_type})

@app.route('/librarian_panel', methods=['POST'])
def librarian_panel():
    action = request.form.get('action', '')
    if action == "backup":
        run_script("backup_script.py")
        return jsonify({"status":"Backup initiated"})
    if action == "restore":
        run_script("restore_script.py")
        return jsonify({"status":"Restore initiated"})
    return jsonify({"status":"Invalid action"}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not is_safe_arg(category):
        return jsonify({"status":"Error","message":"Invalid category"}), 400
    run_script("view_books.py", category)
    return jsonify({"status":"Books retrieval initiated","category":category})

@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    try:
        raw = request.get_data()
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    name = data.get('name')
    member_id = data.get('id')
    membership_date = data.get('membership_date')
    if not name or not member_id:
        return jsonify({"status":"Error","message":"Missing required fields"}), 400
    return jsonify({
        "status":"New member added",
        "name":name,
        "id":member_id,
        "membership_date":membership_date
    })

@app.route('/update_member_details', methods=['POST'])
def update_member_details():
    try:
        raw = request.get_data()
        data = yaml.safe_load(raw.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    member_id = data.get('id')
    new_name = data.get('new_name')
    new_membership_date = data.get('new_membership_date')
    if not member_id:
        return jsonify({"status":"Error","message":"ID required"}), 400
    return jsonify({
        "status":"Member details updated",
        "id":member_id,
        "new_name":new_name,
        "new_membership_date":new_membership_date
    })

if __name__ == "__main__":
    app.run(debug=False)