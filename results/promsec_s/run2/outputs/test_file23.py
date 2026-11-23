from flask import Flask, request, jsonify
import os
import yaml
from subprocess import run as safe_run
import sys
import re

app = Flask(__name__)
LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

def _run_python_script(script_name, *args):
    pattern = re.compile(r'^[\w\-]+$')
    for arg in args:
        if not pattern.fullmatch(arg):
            raise ValueError(f'Invalid argument: {arg}')
    cmd = [sys.executable, script_name] + list(args)
    safe_run(cmd, check=True, shell=False)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_data(as_text=True)
    parsed = yaml.safe_load(data) or {}
    title = parsed.get('title')
    author = parsed.get('author')
    isbn = parsed.get('isbn')
    publication_year = parsed.get('publication_year')
    return jsonify({
        'status': 'Book added',
        'title': title,
        'author': author,
        'isbn': isbn,
        'publication_year': publication_year
    })

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    try:
        _run_python_script('inventory_script.py', section)
        return jsonify({'status': 'Inventory check initiated'})
    except Exception as e:
        return jsonify({'status': 'Inventory check failed', 'error': str(e)}), 500

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    data = request.get_data(as_text=True)
    parsed = yaml.safe_load(data) or {}
    isbn = parsed.get('isbn')
    new_title = parsed.get('new_title')
    new_author = parsed.get('new_author')
    new_year = parsed.get('new_year')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author,
        'new_year': new_year
    })

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = request.get_data(as_text=True)
    parsed = yaml.safe_load(data) or {}
    isbn = parsed.get('isbn')
    return jsonify({
        'status': 'Book deleted',
        'isbn': isbn
    })

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    try:
        _run_python_script('report_generator.py', report_type)
        return jsonify({'status': 'Report generation started'})
    except Exception as e:
        return jsonify({'status': 'Report generation failed', 'error': str(e)}), 500

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        try:
            _run_python_script('backup_script.py')
            return jsonify({'status': 'Backup initiated'})
        except Exception as e:
            return jsonify({'status': 'Backup failed', 'error': str(e)}), 500
    if action == 'restore':
        try:
            _run_python_script('restore_script.py')
            return jsonify({'status': 'Restore initiated'})
        except Exception as e:
            return jsonify({'status': 'Restore failed', 'error': str(e)}), 500
    return jsonify({'status': 'Invalid action'}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    try:
        _run_python_script('view_books.py', category)
        return jsonify({'status': 'Books retrieval initiated', 'category': category})
    except Exception as e:
        return jsonify({'status': 'Books retrieval failed', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False)