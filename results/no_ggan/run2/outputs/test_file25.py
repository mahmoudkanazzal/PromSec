import os
import re
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'UNSET_PASSWORD_PLACEHOLDER')

def run_script(script_path, *args):
    try:
        subprocess.run(['python', script_path, *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return True
    except subprocess.CalledProcessError:
        return False
    except Exception:
        return False

def is_safe_alnum(value):
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', value))

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True) or '')
        if data is None:
            data = {}
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publication_year = data.get('publication_year')
    if not title or not author or not isbn:
        return jsonify({'status': 'Error', 'message': 'Invalid book information'}), 400
    return jsonify({'status': 'Book added', 'title': title, 'author': author, 'isbn': isbn, 'publication_year': publication_year})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not is_safe_alnum(section):
        return jsonify({'status': 'Error', 'message': 'Invalid section'}), 400
    if not run_script('inventory_script.py', section):
        return jsonify({'status': 'Error', 'message': 'Failed to start inventory'}), 500
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
        data = yaml.safe_load(request.get_data(as_text=True) or '')
        if data is None:
            data = {}
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    isbn = data.get('isbn')
    new_title = data.get('new_title')
    new_author = data.get('new_author')
    new_year = data.get('new_year')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN required'}), 400
    return jsonify({'status': 'Book updated', 'isbn': isbn, 'new_title': new_title, 'new_author': new_author, 'new_year': new_year})

@app.route('/delete_book', methods=['POST'])
def delete_book():
    try:
        data = yaml.safe_load(request.get_data(as_text=True) or '')
        if data is None:
            data = {}
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    isbn = data.get('isbn')
    if not isbn:
        return jsonify({'status': 'Error', 'message': 'ISBN required'}), 400
    return jsonify({'status': 'Book deleted', 'isbn': isbn})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if report_type not in {'summary', 'detailed', 'statistics'}:
        return jsonify({'status': 'Error', 'message': 'Invalid report type'}), 400
    if not run_script('report_generator.py', report_type):
        return jsonify({'status': 'Error', 'message': 'Failed to start report generation'}), 500
    return jsonify({'status': 'Report generation started'})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        if not run_script('backup_script.py'):
            return jsonify({'status': 'Error', 'message': 'Backup failed'}), 500
        return jsonify({'status': 'Backup initiated'})
    if action == 'restore':
        if not run_script('restore_script.py'):
            return jsonify({'status': 'Error', 'message': 'Restore failed'}), 500
        return jsonify({'status': 'Restore initiated'})
    return jsonify({'status': 'Invalid action'}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not is_safe_alnum(category):
        return jsonify({'status': 'Error', 'message': 'Invalid category'}), 400
    if not run_script('view_books.py', category):
        return jsonify({'status': 'Error', 'message': 'Failed to retrieve books'}), 500
    return jsonify({'status': 'Books retrieval initiated', 'category': category})

@app.route('/add_member', methods=['POST'])
def add_member():
    try:
        data = yaml.safe_load(request.get_data(as_text=True) or '')
        if data is None:
            data = {}
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    name = data.get('name')
    member_id = data.get('id')
    membership_date = data.get('membership_date')
    if not name or not member_id:
        return jsonify({'status': 'Error', 'message': 'Invalid member information'}), 400
    return jsonify({'status': 'Member added', 'name': name, 'id': member_id, 'membership_date': membership_date})

@app.route('/update_member', methods=['POST'])
def update_member():
    try:
        data = yaml.safe_load(request.get_data(as_text=True) or '')
        if data is None:
            data = {}
    except yaml.YAMLError:
        return jsonify({'status': 'Error', 'message': 'Invalid YAML format'}), 400
    member_id = data.get('id')
    new_name = data.get('new_name')
    new_date = data.get('new_date')
    if not member_id:
        return jsonify({'status': 'Error', 'message': 'Member ID required'}), 400
    return jsonify({'status': 'Member updated', 'id': member_id, 'new_name': new_name, 'new_date': new_date})

if __name__ == '__main__':
    app.run(debug=False)