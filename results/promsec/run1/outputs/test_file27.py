import os, re, sys, runpy
from flask import Flask, request, jsonify
import yaml

_SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts'))
_allowed_scripts = {'run_inventory.py', 'report_generator.py', 'backup_script.py', 'restore_script.py', 'view_books.py'}
librarian_password = os.getenv('LIBRARIAN_PASSWORD')
_param_regex = re.compile(r'^[A-Za-z0-9_]{1,64}$')

def validate_param(value):
    return isinstance(value, str) and _param_regex.fullmatch(value) is not None

def _is_path_within_directory(base_dir, target_path):
    base_dir = os.path.abspath(base_dir)
    target_path = os.path.abspath(target_path)
    return os.path.commonpath([base_dir, target_path]) == base_dir

def run_script(script_name, *args):
    try:
        if script_name not in _allowed_scripts:
            return False
        for arg in args:
            if not validate_param(arg):
                return False
        script_path = os.path.join(_SCRIPTS_DIR, script_name)
        if not _is_path_within_directory(_SCRIPTS_DIR, script_path):
            return False
        if not os.path.isfile(script_path):
            return False
        original_argv = sys.argv
        sys.argv = [script_path] + list(args)
        try:
            runpy.run_path(script_path, run_name='__main__')
        finally:
            sys.argv = original_argv
        return True
    except Exception:
        return False

app = Flask(__name__)

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must be a mapping'), 400
    for key in ('title', 'author', 'isbn'):
        if key not in data:
            return jsonify(error=f'Missing {key}'), 400
    response = {'status': 'New Book added', 'title': data['title'], 'author': data['author'], 'isbn': data['isbn']}
    if 'genre' in data:
        response['genre'] = data['genre']
    if 'publication_year' in data:
        response['publication_year'] = data['publication_year']
    return jsonify(response)

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not validate_param(section):
        return jsonify(error='Invalid section'), 400
    if not run_script('run_inventory.py', section):
        return jsonify(error='Script execution failed'), 500
    return jsonify(status='Inventory check started', section=section)

@app.route('/admin_access', methods=['POST'])
def admin_access():
    if librarian_password is None:
        return jsonify(error='Configuration error'), 500
    password = request.form.get('password', '')
    if password == librarian_password:
        return jsonify(status='Admin access granted')
    return jsonify(error='Access denied'), 401

@app.route('/update_book_details', methods=['POST'])
def update_book_details():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must be a mapping'), 400
    if 'isbn' not in data:
        return jsonify(error='Missing isbn'), 400
    response = {'status': 'Book details updated', 'isbn': data['isbn']}
    for key in ('new_title', 'new_author', 'new_genre', 'new_publication_year'):
        if key in data:
            response[key] = data[key]
    return jsonify(response)

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must be a mapping'), 400
    if 'isbn' not in data:
        return jsonify(error='Missing isbn'), 400
    return jsonify(status='Book deleted', isbn=data['isbn'])

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if not validate_param(report_type):
        return jsonify(error='Invalid type'), 400
    if not run_script('report_generator.py', report_type):
        return jsonify(error='Script execution failed'), 500
    return jsonify(status='Report generation started', type=report_type)

@app.route('/librarian_panel', methods=['POST'])
def librarian_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        if run_script('backup_script.py'):
            return jsonify(status='Backup initiated')
        return jsonify(error='Backup failed'), 500
    if action == 'restore':
        if run_script('restore_script.py'):
            return jsonify(status='Restore initiated')
        return jsonify(error='Restore failed'), 500
    return jsonify(error='Invalid action'), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not validate_param(category):
        return jsonify(error='Invalid category'), 400
    if not run_script('view_books.py', category):
        return jsonify(error='Script execution failed'), 500
    return jsonify(status='Books retrieval initiated', category=category)

@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must be a mapping'), 400
    for key in ('name', 'id'):
        if key not in data:
            return jsonify(error=f'Missing {key}'), 400
    response = {'status': 'New member added', 'name': data['name'], 'id': data['id']}
    if 'membership_date' in data:
        response['membership_date'] = data['membership_date']
    return jsonify(response)

@app.route('/update_member_details', methods=['POST'])
def update_member_details():
    try:
        data = yaml.safe_load(request.data)
    except Exception:
        return jsonify(error='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(error='YAML must be a mapping'), 400
    if 'id' not in data:
        return jsonify(error='Missing id'), 400
    response = {'status': 'Member details updated', 'id': data['id']}
    for key in ('new_name', 'new_membership_date'):
        if key in data:
            response[key] = data[key]
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)