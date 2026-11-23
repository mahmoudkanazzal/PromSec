import os
import re
import yaml
import hmac
import importlib.util
from flask import Flask, request, jsonify

app = Flask(__name__)

def _is_valid_token(token: str) -> bool:
    if not token:
        return False
    return re.fullmatch(r'[\w-]+', token) is not None

_ALLOWED_SCRIPTS = {
    'inventory_script.py',
    'report_generator.py',
    'backup_script.py',
    'restore_script.py',
    'view_books.py'
}

def _run_script(script_name: str, args: list):
    if script_name not in _ALLOWED_SCRIPTS:
        raise ValueError('Invalid script name')
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    if not os.path.isfile(script_path):
        raise FileNotFoundError
    spec = importlib.util.spec_from_file_location('_dynamic_module', script_path)
    if spec is None or spec.loader is None:
        raise ImportError('Cannot load script')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, 'main') and callable(module.main):
        module.main(*args)
    elif hasattr(module, 'run') and callable(module.run):
        module.run(*args)

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    required = ['title', 'author', 'isbn', 'publication_year']
    for key in required:
        if key not in data:
            return jsonify({'error': f'Missing field: {key}'}), 400
    response = {
        'status': 'Book added',
        'title': data['title'],
        'author': data['author'],
        'isbn': data['isbn'],
        'publication_year': data['publication_year']
    }
    return jsonify(response), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not _is_valid_token(section):
        return jsonify({'error': 'Invalid section parameter'}), 400
    try:
        _run_script('inventory_script.py', [section])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'Inventory check initiated'}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    env_password = os.getenv('LIBRARIAN_PASSWORD', '')
    if hmac.compare_digest(password, env_password):
        return jsonify({'status': 'Librarian access granted'}), 200
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if 'isbn' not in data:
        return jsonify({'error': 'Missing field: isbn'}), 400
    response = {
        'status': 'Book updated',
        'isbn': data['isbn'],
        'new_title': data.get('title'),
        'new_author': data.get('author'),
        'new_year': data.get('publication_year')
    }
    return jsonify(response), 200

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        return jsonify({'error': 'Invalid YAML'}), 400
    if 'isbn' not in data:
        return jsonify({'error': 'Missing field: isbn'}), 400
    return jsonify({'status': 'Book deleted', 'isbn': data['isbn']}), 200

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if not _is_valid_token(report_type):
        return jsonify({'error': 'Invalid report type'}), 400
    try:
        _run_script('report_generator.py', [report_type])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'Report generation started'}), 200

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        try:
            _run_script('backup_script.py', [])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        return jsonify({'status': 'Backup initiated'}), 200
    if action == 'restore':
        try:
            _run_script('restore_script.py', [])
        except Exception as e:
            return jsonify({'error': str(e)}), 500
        return jsonify({'status': 'Restore initiated'}), 200
    return jsonify({'status': 'Invalid action'}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not _is_valid_token(category):
        return jsonify({'error': 'Invalid category parameter'}), 400
    try:
        _run_script('view_books.py', [category])
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    return jsonify({'status': 'Books retrieval initiated', 'category': category}), 200

if __name__ == '__main__':
    app.run(debug=False)