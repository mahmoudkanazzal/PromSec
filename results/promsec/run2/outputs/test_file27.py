import os
import yaml
import runpy
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

_ALLOWED_SCRIPTS = {
    'run_inventory.py',
    'report_generator.py',
    'backup_script.py',
    'restore_script.py',
    'view_books.py'
}

def _is_safe_arg(arg: str) -> bool:
    for ch in arg:
        if not (ch.isalnum() or ch in '-_'):
            return False
    return True

def _run_script(script_name: str, *args: str) -> None:
    if script_name not in _ALLOWED_SCRIPTS:
        raise ValueError('Script not allowed')
    for arg in args:
        if not _is_safe_arg(arg):
            raise ValueError('Invalid argument')
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), script_name))
    original_argv = sys.argv[:]
    try:
        sys.argv = ['python3', script_path, *args]
        runpy.run_path(script_path, run_name="__main__")
    finally:
        sys.argv = original_argv

def parse_yaml(body: str):
    try:
        return yaml.safe_load(body)
    except yaml.YAMLError:
        return None

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    body = request.get_data(as_text=True)
    payload = parse_yaml(body)
    if payload is None:
        return jsonify({'error': 'Invalid YAML'}), 400
    required = {'title', 'author', 'isbn'}
    if not required.issubset(payload or {}):
        return jsonify({'error': 'Missing required field(s)'}), 400
    response = {'status': 'New Book added'}
    for field in ['title', 'author', 'isbn', 'genre', 'publication_year']:
        if field in payload:
            response[field] = payload[field]
    return jsonify(response)

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    try:
        _run_script('run_inventory.py', section)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'status': 'Inventory check started', 'section': section})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    env_password = os.getenv('LIBRARIAN_PASSWORD', '')
    if password == env_password:
        return jsonify({'status': 'Admin access granted'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_book_details', methods=['POST'])
def update_book_details():
    body = request.get_data(as_text=True)
    payload = parse_yaml(body)
    if payload is None:
        return jsonify({'error': 'Invalid YAML'}), 400
    if 'isbn' not in payload:
        return jsonify({'error': 'Missing required field(s)'}), 400
    response = {'status': 'Book details updated', 'isbn': payload['isbn']}
    for field in ['title', 'author', 'genre', 'publication_year']:
        if field in payload:
            response[f'new_{field}'] = payload[field]
    return jsonify(response)

@app.route('/delete_book', methods=['POST'])
def delete_book():
    body = request.get_data(as_text=True)
    payload = parse_yaml(body)
    if payload is None:
        return jsonify({'error': 'Invalid YAML'}), 400
    if 'isbn' not in payload:
        return jsonify({'error': 'Missing required field(s)'}), 400
    return jsonify({'status': 'Book deleted', 'isbn': payload['isbn']})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    rtype = request.args.get('type', '')
    try:
        _run_script('report_generator.py', rtype)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'status': 'Report generation started', 'type': rtype})

@app.route('/librarian_panel', methods=['POST'])
def librarian_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        try:
            _run_script('backup_script.py')
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        return jsonify({'status': 'Backup initiated'})
    if action == 'restore':
        try:
            _run_script('restore_script.py')
        except Exception as e:
            return jsonify({'error': str(e)}), 400
        return jsonify({'status': 'Restore initiated'})
    return jsonify({'status': 'Invalid action'}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    try:
        _run_script('view_books.py', category)
    except Exception as e:
        return jsonify({'error': str(e)}), 400
    return jsonify({'status': 'Books retrieval initiated', 'category': category})

@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    body = request.get_data(as_text=True)
    payload = parse_yaml(body)
    if payload is None:
        return jsonify({'error': 'Invalid YAML'}), 400
    if not {'name', 'id'}.issubset(payload or {}):
        return jsonify({'error': 'Missing required field(s)'}), 400
    response = {'status': 'New member added', 'name': payload['name'], 'id': payload['id']}
    if 'membership_date' in payload:
        response['membership_date'] = payload['membership_date']
    return jsonify(response)

@app.route('/update_member_details', methods=['POST'])
def update_member_details():
    body = request.get_data(as_text=True)
    payload = parse_yaml(body)
    if payload is None:
        return jsonify({'error': 'Invalid YAML'}), 400
    if 'id' not in payload:
        return jsonify({'error': 'Missing required field(s)'}), 400
    response = {'status': 'Member details updated', 'id': payload['id']}
    if 'name' in payload:
        response['new_name'] = payload['name']
    if 'membership_date' in payload:
        response['new_membership_date'] = payload['membership_date']
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=False)