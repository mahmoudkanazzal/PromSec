import os
import yaml
import re
import hmac
import importlib.util
import runpy
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

SCRIPTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), 'scripts'))

def is_safe_token(token: str) -> bool:
    return bool(re.fullmatch(r'^[A-Za-z0-9_-]+$', token))

def run_script(script_name: str, *args):
    script_path = os.path.abspath(os.path.join(SCRIPTS_DIR, script_name))
    if not os.path.commonpath([SCRIPTS_DIR, script_path]) == SCRIPTS_DIR:
        raise ValueError('Invalid script path')
    spec = importlib.util.spec_from_file_location('script_module', script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if hasattr(module, 'main') and callable(module.main):
        return module.main(*args)
    old_argv = sys.argv
    sys.argv = [script_path] + [str(a) for a in args]
    try:
        result = runpy.run_path(script_path)
    finally:
        sys.argv = old_argv
    return result

@app.route('/add_book', methods=['POST'])
def add_book():
    data = yaml.safe_load(request.data)
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    publication_year = data.get('publication_year')
    return jsonify({
        'title': title,
        'author': author,
        'isbn': isbn,
        'publication_year': publication_year,
        'status': 'Book added'
    })

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not is_safe_token(section):
        return jsonify({'status': 'Invalid section parameter'}), 400
    allowed = {'fiction', 'nonfiction', 'reference', 'children', 'science'}
    if section not in allowed:
        return jsonify({'status': 'Section not allowed'}), 400
    try:
        run_script('inventory_script.py', section)
    except Exception:
        return jsonify({'status': 'Inventory script failed'}), 500
    return jsonify({'status': 'Inventory check initiated'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    if LIBRARIAN_PASSWORD is None:
        return jsonify({'status': 'Server configuration error'}), 500
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    data = yaml.safe_load(request.data)
    isbn = data.get('isbn')
    new_title = data.get('new_title')
    new_author = data.get('new_author')
    new_year = data.get('new_year')
    response = {'status': 'Book updated', 'isbn': isbn}
    if new_title is not None:
        response['new_title'] = new_title
    if new_author is not None:
        response['new_author'] = new_author
    if new_year is not None:
        response['new_year'] = new_year
    return jsonify(response)

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = yaml.safe_load(request.data)
    isbn = data.get('isbn')
    return jsonify({'status': 'Book deleted', 'isbn': isbn})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    allowed = {'summary', 'detailed', 'statistics'}
    if report_type not in allowed:
        return jsonify({'status': 'Invalid report type'}), 400
    try:
        run_script('report_generator.py', report_type)
    except Exception:
        return jsonify({'status': 'Report generation failed'}), 500
    return jsonify({'status': 'Report generation started'})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        try:
            run_script('backup_script.py')
        except Exception:
            return jsonify({'status': 'Backup failed'}), 500
        return jsonify({'status': 'Backup initiated'})
    if action == 'restore':
        try:
            run_script('restore_script.py')
        except Exception:
            return jsonify({'status': 'Restore failed'}), 500
        return jsonify({'status': 'Restore initiated'})
    return jsonify({'status': 'Invalid action'}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not is_safe_token(category):
        return jsonify({'status': 'Invalid category parameter'}), 400
    allowed = {'fiction', 'nonfiction', 'reference', 'children', 'science'}
    if category not in allowed:
        return jsonify({'status': 'Category not allowed'}), 400
    try:
        run_script('view_books.py', category)
    except Exception:
        return jsonify({'status': 'Books retrieval failed'}), 500
    return jsonify({'status': 'Books retrieval initiated', 'category': category})

if __name__ == '__main__':
    app.run(debug=False)