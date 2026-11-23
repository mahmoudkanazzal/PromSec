import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify, abort

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if LIBRARIAN_PASSWORD is None:
    raise RuntimeError('Environment variable LIBRARIAN_PASSWORD must be set')


def _run_script(script_path: str, arg: str = None):
    try:
        if arg is not None:
            if not re.fullmatch(r'^[A-Za-z0-9_-]+$', arg):
                abort(400, description='Invalid argument supplied')
            cmd = ['python', script_path, arg]
        else:
            cmd = ['python', script_path]
        subprocess.run(cmd, check=False, capture_output=True, text=True)
    except Exception as e:
        abort(500, description=str(e))


@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Invalid YAML payload')
    required = {'title', 'author', 'isbn', 'publication_year'}
    if not required.issubset(data):
        abort(400, description='Missing required book fields')
    return jsonify({
        'status': 'Book added',
        'title': data['title'],
        'author': data['author'],
        'isbn': data['isbn'],
        'publication_year': data['publication_year']
    })


@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    _run_script('inventory_script.py', section if section else None)
    return jsonify({'status': 'Inventory check initiated'})


@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401


@app.route('/update_book', methods=['POST'])
def update_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Invalid YAML payload')
    isbn = data.get('isbn')
    if not isbn:
        abort(400, description='Missing ISBN for update')
    new_title = data.get('new_title', '')
    new_author = data.get('new_author', '')
    new_year = data.get('new_year', '')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author,
        'new_year': new_year
    })


@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True))
    except yaml.YAMLError:
        abort(400, description='Invalid YAML payload')
    if not isinstance(data, dict):
        abort(400, description='Invalid YAML payload')
    isbn = data.get('isbn')
    if not isbn:
        abort(400, description='Missing ISBN for deletion')
    return jsonify({'status': 'Book deleted', 'isbn': isbn})


@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    _run_script('report_generator.py', report_type if report_type else None)
    return jsonify({'status': 'Report generation started'})


@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        _run_script('backup_script.py')
        return jsonify({'status': 'Backup initiated'})
    if action == 'restore':
        _run_script('restore_script.py')
        return jsonify({'status': 'Restore initiated'})
    return jsonify({'status': 'Invalid action'}), 400


@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    _run_script('view_books.py', category if category else None)
    return jsonify({'status': 'Books retrieval initiated', 'category': category})


if __name__ == '__main__':
    app.run(debug=False)