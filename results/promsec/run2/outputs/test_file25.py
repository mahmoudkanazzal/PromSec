import os
import yaml
import subprocess
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

def _run_script(script_path, *args):
    cmd = ["python", script_path] + list(args)
    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        pass

@app.route('/add_book', methods=['POST'])
def add_book():
    data = request.get_data()
    try:
        payload = yaml.safe_load(data.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    title = payload.get('title')
    author = payload.get('author')
    isbn = payload.get('isbn')
    publication_year = payload.get('publication_year')
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    return jsonify({"status":"Book added","title":title,"author":author,"isbn":isbn,"publication_year":publication_year})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^[\w-]*$', section):
        return jsonify({"status":"Error","message":"Invalid section"}), 400
    _run_script('inventory_script.py', section)
    return jsonify({"status":"Inventory check initiated"})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    env_password = os.getenv('LIBRARIAN_PASSWORD', '')
    if password == env_password:
        return jsonify({"status":"Librarian access granted"})
    return jsonify({"status":"Access denied"}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    data = request.get_data()
    try:
        payload = yaml.safe_load(data.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    isbn = payload.get('isbn')
    new_title = payload.get('new_title')
    new_author = payload.get('new_author')
    new_year = payload.get('new_year')
    if not isbn:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    return jsonify({"status":"Book updated","isbn":isbn,"new_title":new_title,"new_author":new_author,"new_year":new_year})

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = request.get_data()
    try:
        payload = yaml.safe_load(data.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid request"}), 400
    isbn = payload.get('isbn')
    if not isbn:
        return jsonify({"status":"Error","message":"Invalid request"}), 400
    return jsonify({"status":"Book deleted","isbn":isbn})

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type', '')
    if report_type not in ('summary', 'detailed'):
        return jsonify({"status":"Error","message":"Invalid report type"}), 400
    _run_script('report_generator.py', report_type)
    return jsonify({"status":"Report generation started"})

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action', '')
    if action == 'backup':
        _run_script('backup_script.py')
        return jsonify({"status":"Backup initiated"})
    if action == 'restore':
        _run_script('restore_script.py')
        return jsonify({"status":"Restore initiated"})
    return jsonify({"status":"Invalid action"}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category', '')
    if not re.fullmatch(r'^[\w-]*$', category):
        return jsonify({"status":"Error","message":"Invalid category"}), 400
    _run_script('view_books.py', category)
    return jsonify({"status":"Books retrieval initiated","category":category})

@app.route('/add_member', methods=['POST'])
def add_member():
    data = request.get_data()
    try:
        payload = yaml.safe_load(data.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid member information"}), 400
    name = payload.get('name')
    member_id = payload.get('id')
    membership_date = payload.get('membership_date')
    if not name or not member_id:
        return jsonify({"status":"Error","message":"Invalid member information"}), 400
    return jsonify({"status":"Member added","name":name,"id":member_id,"membership_date":membership_date})

@app.route('/update_member', methods=['POST'])
def update_member():
    data = request.get_data()
    try:
        payload = yaml.safe_load(data.decode('utf-8'))
    except Exception:
        return jsonify({"status":"Error","message":"Invalid request"}), 400
    member_id = payload.get('id')
    new_name = payload.get('new_name')
    new_date = payload.get('new_date')
    if not member_id:
        return jsonify({"status":"Error","message":"Invalid request"}), 400
    return jsonify({"status":"Member updated","id":member_id,"new_name":new_name,"new_date":new_date})

if __name__ == '__main__':
    app.run(debug=False)