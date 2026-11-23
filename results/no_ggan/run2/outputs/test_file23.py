import os
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if LIBRARIAN_PASSWORD is None:
    raise RuntimeError('Environment variable LIBRARIAN_PASSWORD is not set')

def run_script(script_name, *args):
    cmd = ['python', script_name] + list(args)
    subprocess.run(cmd, shell=False, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_data().decode('utf-8')
    payload = yaml.safe_load(data) or {}
    title = payload.get('title', '')
    author = payload.get('author', '')
    isbn = payload.get('isbn', '')
    publication_year = payload.get('publication_year', '')
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
    run_script('inventory_script.py', section)
    return jsonify({'status': 'Inventory check initiated'})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({'status': 'Librarian access granted'})
    return jsonify({'status': 'Access denied'}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    data = request.get_data().decode('utf-8')
    payload = yaml.safe_load(data) or {}
    isbn = payload.get('isbn', '')
    new_title = payload.get('new_title', '')
    new_author = payload.get('new_author', '')
    new_year = payload.get('new_year', '')
    return jsonify({
        'status': 'Book updated',
        'isbn': isbn,
        'new_title': new_title,
        'new_author': new_author,
        'new_year': new_year
    })

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = request.get_data().decode('utf-8')
    payload = yaml.safe_load(data) or {}
    isbn = payload.get('isbn', '')
    return jsonify({
        'status': 'Book deleted',
        'isbn': isbn
    })

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    run_script('report_generator.py', report_type)
    return jsonify({'status': 'Report generation started'})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        run_script('backup_script.py')
        return jsonify({'status': 'Backup initiated'})
    if action == 'restore':
        run_script('restore_script.py')
        return jsonify({'status': 'Restore initiated'})
    return jsonify({'status': 'Invalid action'}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    run_script('view_books.py', category)
    return jsonify({
        'status': 'Books retrieval initiated',
        'category': category
    })

if __name__ == '__main__':
    app.run(debug=False)