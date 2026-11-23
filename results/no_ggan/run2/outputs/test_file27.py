import os
import re
import subprocess
import hmac
from flask import Flask, request, jsonify, abort
import yaml

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if LIBRARIAN_PASSWORD is None:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD must be set")

SAFE_ARG_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")

def _run_script(script_name: str, arg: str = None):
    cmd = ["python3", script_name]
    if arg is not None:
        if not SAFE_ARG_PATTERN.fullmatch(arg):
            abort(400, description="Invalid argument supplied")
        cmd.append(arg)
    subprocess.run(cmd, check=False)

def _load_yaml():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
        if not isinstance(data, dict):
            data = {}
        return data
    except yaml.YAMLError:
        abort(400, jsonify({"status":"Error","message":"Invalid YAML format"}))

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    data = _load_yaml()
    title = data.get('title', '')
    author = data.get('author', '')
    isbn = data.get('isbn', '')
    genre = data.get('genre', '')
    publication_year = data.get('publication_year', '')
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Missing book information"}), 400
    return jsonify({"status":"New Book added","title":title,"author":author,"isbn":isbn,"genre":genre,"publication_year":publication_year})

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    _run_script("run_inventory.py", section)
    return jsonify({"status":"Inventory check started","section":section})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({"status":"Admin access granted"})
    return jsonify({"status":"Access denied"}), 401

@app.route('/update_book_details', methods=['POST'])
def update_book_details():
    data = _load_yaml()
    isbn = data.get('isbn', '')
    new_title = data.get('new_title', '')
    new_author = data.get('new_author', '')
    new_genre = data.get('new_genre', '')
    new_publication_year = data.get('new_publication_year', '')
    if not isbn:
        return jsonify({"status":"Error","message":"Missing book information"}), 400
    return jsonify({"status":"Book details updated","isbn":isbn,"new_title":new_title,"new_author":new_author,"new_genre":new_genre,"new_publication_year":new_publication_year})

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = _load_yaml()
    isbn = data.get('isbn', '')
    if not isbn:
        return jsonify({"status":"Error","message":"Missing book information"}), 400
    return jsonify({"status":"Book deleted","isbn":isbn})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    rtype = request.args.get('type', '')
    _run_script("report_generator.py", rtype)
    return jsonify({"status":"Report generation started","type":rtype})

@app.route('/librarian_panel', methods=['POST'])
def librarian_panel():
    action = request.form.get('action', '')
    if action == "backup":
        _run_script("backup_script.py")
        return jsonify({"status":"Backup initiated"})
    if action == "restore":
        _run_script("restore_script.py")
        return jsonify({"status":"Restore initiated"})
    return jsonify({"status":"Invalid action"}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    _run_script("view_books.py", category)
    return jsonify({"status":"Books retrieval initiated","category":category})

@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    data = _load_yaml()
    name = data.get('name', '')
    member_id = data.get('id', '')
    membership_date = data.get('membership_date', '')
    if not name or not member_id:
        return jsonify({"status":"Error","message":"Missing book information"}), 400
    return jsonify({"status":"New member added","name":name,"id":member_id,"membership_date":membership_date})

@app.route('/update_member_details', methods=['POST'])
def update_member_details():
    data = _load_yaml()
    member_id = data.get('id', '')
    new_name = data.get('new_name', '')
    new_membership_date = data.get('new_membership_date', '')
    if not member_id:
        return jsonify({"status":"Error","message":"Missing book information"}), 400
    return jsonify({"status":"Member details updated","id":member_id,"new_name":new_name,"new_membership_date":new_membership_date})

if __name__ == "__main__":
    app.run(debug=False)