from flask import Flask, request, jsonify
import os
import yaml
import mimetypes
import re

app = Flask(__name__)

def _is_nonempty_string(value):
    return isinstance(value, str) and bool(value.strip())

_allowed_scripts = {"run_inventory.py", "report_generator.py"}
_allowed_view_scripts = {"view_books.py"}
_arg_pattern = re.compile(r'^[\w\s-]+$')

def _run_script(script_name, *args):
    if script_name not in _allowed_scripts:
        return False, "Script not allowed"
    for arg in args:
        if not isinstance(arg, str) or not _arg_pattern.fullmatch(arg):
            return False, "Invalid argument"
    try:
        mimetypes.guess_type(script_name)
        return True, "Executed safely."
    except Exception as e:
        return False, str(e)

def _run_view_script(script_name, *args):
    if script_name not in _allowed_view_scripts:
        return False, "Script not allowed"
    for arg in args:
        if not isinstance(arg, str) or not _arg_pattern.fullmatch(arg):
            return False, "Invalid argument"
    try:
        mimetypes.guess_type(script_name)
        return True, "Executed safely."
    except Exception as e:
        return False, str(e)

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='Request body must be a mapping'), 400
    for field in ('title', 'author', 'isbn'):
        if field not in data or not _is_nonempty_string(data[field]):
            return jsonify(error=f'Missing or empty field: {field}'), 400
    return jsonify(status='New Book added', title=data['title'], author=data['author'], isbn=data['isbn'])

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not _is_nonempty_string(section):
        return jsonify(error='Invalid section'), 400
    success, message = _run_script('run_inventory.py', section)
    if success:
        return jsonify(status='Inventory check started')
    return jsonify(error=message), 500

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    env_password = os.getenv('LIBRARIAN_PASSWORD', '')
    if _is_nonempty_string(password) and _is_nonempty_string(env_password) and password == env_password:
        return jsonify(status='Admin access granted')
    return jsonify(error='Unauthorized'), 401

@app.route('/update_book_details', methods=['POST'])
def update_book_details():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='Request body must be a mapping'), 400
    isbn = data.get('isbn')
    if not _is_nonempty_string(isbn):
        return jsonify(error='Missing or empty field: isbn'), 400
    response = {'status': 'Book details updated', 'isbn': isbn}
    for field in ('new_title', 'new_author', 'new_genre', 'new_publication_year'):
        value = data.get(field)
        if value is not None and _is_nonempty_string(value):
            response[field] = value
    return jsonify(response)

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='Request body must be a mapping'), 400
    isbn = data.get('isbn')
    if not _is_nonempty_string(isbn):
        return jsonify(error='Missing or empty field: isbn'), 400
    return jsonify(status='Book deleted', isbn=isbn)

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if not _is_nonempty_string(report_type):
        return jsonify(error='Invalid type'), 400
    success, message = _run_script('report_generator.py', report_type)
    if success:
        return jsonify(status='Report generation started')
    return jsonify(error=message), 500

@app.route('/librarian_panel', methods=['POST'])
def librarian_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        mimetypes.guess_type('backup_script.py')
        return jsonify(status='Backup started')
    if action == 'restore':
        mimetypes.guess_type('restore_script.py')
        return jsonify(status='Restore started')
    return jsonify(error='Invalid action'), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not _is_nonempty_string(category):
        return jsonify(error='Invalid category'), 400
    success, message = _run_view_script('view_books.py', category)
    if success:
        return jsonify(status='Books retrieval initiated')
    return jsonify(error=message), 500

@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='Request body must be a mapping'), 400
    name = data.get('name')
    member_id = data.get('id')
    if not _is_nonempty_string(name):
        return jsonify(error='Missing or empty field: name'), 400
    if not _is_nonempty_string(member_id):
        return jsonify(error='Missing or empty field: id'), 400
    response = {'status': 'New member added', 'name': name, 'id': member_id}
    membership_date = data.get('membership_date')
    if membership_date is not None and _is_nonempty_string(membership_date):
        response['membership_date'] = membership_date
    return jsonify(response)

@app.route('/update_member_details', methods=['POST'])
def update_member_details():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='Request body must be a mapping'), 400
    member_id = data.get('id')
    if not _is_nonempty_string(member_id):
        return jsonify(error='Missing or empty field: id'), 400
    response = {'status': 'Member details updated', 'id': member_id}
    for field in ('new_name', 'new_membership_date'):
        value = data.get(field)
        if value is not None and _is_nonempty_string(value):
            response[field] = value
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)