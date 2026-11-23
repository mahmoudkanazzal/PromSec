import os
import re
import yaml
import subprocess
from flask import Flask, request, jsonify

admin_password = os.getenv('LIBRARIAN_PASSWORD')
if not admin_password:
    raise RuntimeError('LIBRARIAN_PASSWORD environment variable not set')

app = Flask(__name__)
token_pattern = re.compile(r'^[A-Za-z0-9_.-]+$')


def validate_token(token):
    return token is not None and token_pattern.fullmatch(token)


def run_script(script, token=None):
    args = ['python3', script]
    if token is not None:
        args.append(token)
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def yaml_load(body):
    try:
        data = yaml.safe_load(body)
        if data is None:
            data = {}
        return data, None
    except yaml.YAMLError:
        return None, jsonify({'status': 'Error', 'message': 'Invalid YAML'}), 400


@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    body = request.get_data(as_text=True)
    data, error_resp, status = yaml_load(body)
    if error_resp:
        return error_resp, status
    required = ['title', 'author', 'isbn']
    if not all(k in data for k in required):
        return jsonify({'status': 'Error', 'message': 'Missing book information'}), 400
    response = {
        'status': 'New Book added',
        'title': data.get('title'),
        'author': data.get('author'),
        'isbn': data.get('isbn'),
        'genre': data.get('genre'),
        'publication_year': data.get('publication_year')
    }
    return jsonify(response)


@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section')
    if not validate_token(section):
        return jsonify({'status': 'Error', 'message': 'Invalid token'}), 400
    try:
        run_script('run_inventory.py', section)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Failed to start inventory check'}), 500
    return jsonify({'status': 'Inventory check started', 'section': section})


@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password')
    if password == admin_password:
        return jsonify({'status': 'Admin access granted'})
    return jsonify({'status': 'Access denied'}), 401


@app.route('/update_book_details', methods=['POST'])
def update_book_details():
    body = request.get_data(as_text=True)
    data, error_resp, status = yaml_load(body)
    if error_resp:
        return error_resp, status
    if 'isbn' not in data:
        return jsonify({'status': 'Error', 'message': 'Missing book information'}), 400
    response = {
        'status': 'Book details updated',
        'isbn': data.get('isbn'),
        'new_title': data.get('new_title'),
        'new_author': data.get('new_author'),
        'new_genre': data.get('new_genre'),
        'new_publication_year': data.get('new_publication_year')
    }
    return jsonify(response)


@app.route('/delete_book', methods=['POST'])
def delete_book():
    body = request.get_data(as_text=True)
    data, error_resp, status = yaml_load(body)
    if error_resp:
        return error_resp, status
    if 'isbn' not in data:
        return jsonify({'status': 'Error', 'message': 'Missing book information'}), 400
    return jsonify({'status': 'Book deleted', 'isbn': data.get('isbn')})


@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type')
    if not validate_token(report_type):
        return jsonify({'status': 'Error', 'message': 'Invalid token'}), 400
    try:
        run_script('report_generator.py', report_type)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Failed to start report generation'}), 500
    return jsonify({'status': 'Report generation started', 'type': report_type})


@app.route('/librarian_panel', methods=['POST'])
def librarian_panel():
    action = request.form.get('action')
    if action not in ('backup', 'restore'):
        return jsonify({'status': 'Invalid action'}), 400
    script = 'backup_script.py' if action == 'backup' else 'restore_script.py'
    try:
        run_script(script)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': f'{action.capitalize()} failed'}), 500
    return jsonify({'status': f'{action.capitalize()} initiated'})


@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category')
    if not validate_token(category):
        return jsonify({'status': 'Error', 'message': 'Invalid token'}), 400
    try:
        run_script('view_books.py', category)
    except subprocess.CalledProcessError:
        return jsonify({'status': 'Error', 'message': 'Failed to retrieve books'}), 500
    return jsonify({'status': 'Books retrieval initiated', 'category': category})


@app.route('/add_new_member', methods=['POST'])
def add_new_member():
    body = request.get_data(as_text=True)
    data, error_resp, status = yaml_load(body)
    if error_resp:
        return error_resp, status
    required = ['name', 'id']
    if not all(k in data for k in required):
        return jsonify({'status': 'Error', 'message': 'Missing member information'}), 400
    response = {
        'status': 'New member added',
        'name': data.get('name'),
        'id': data.get('id'),
        'membership_date': data.get('membership_date')
    }
    return jsonify(response)


@app.route('/update_member_details', methods=['POST'])
def update_member_details():
    body = request.get_data(as_text=True)
    data, error_resp, status = yaml_load(body)
    if error_resp:
        return error_resp, status
    if 'id' not in data:
        return jsonify({'status': 'Error', 'message': 'Missing member information'}), 400
    response = {
        'status': 'Member details updated',
        'id': data.get('id'),
        'new_name': data.get('new_name'),
        'new_membership_date': data.get('new_membership_date')
    }
    return jsonify(response)


if __name__ == '__main__':
    app.run(debug=False)