from flask import Flask, request, jsonify
import yaml
import os

app = Flask(__name__)

def is_valid_identifier(value):
    return isinstance(value, str) and value != '' and value.isidentifier()

try:
    from inventory_script import main as inventory_main
except Exception:
    inventory_main = None
try:
    from report_generator import main as report_main
except Exception:
    report_main = None
try:
    from backup_script import main as backup_main
except Exception:
    backup_main = None
try:
    from restore_script import main as restore_main
except Exception:
    restore_main = None
try:
    from view_books import main as view_books_main
except Exception:
    view_books_main = None

def parse_yaml_body():
    try:
        data = yaml.safe_load(request.data)
        if not isinstance(data, dict):
            return None
        return data
    except Exception:
        return None

@app.route('/add_book', methods=['POST'])
def add_book():
    data = parse_yaml_body()
    if not data or not all(k in data for k in ('title', 'author', 'isbn')):
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    response = {
        "status":"Book added",
        "title":data.get('title'),
        "author":data.get('author'),
        "isbn":data.get('isbn'),
        "publication_year":data.get('publication_year')
    }
    return jsonify(response), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    if not is_valid_identifier(section):
        return jsonify({"status":"Error","message":"Invalid section parameter"}), 400
    if inventory_main is None:
        return jsonify({"status":"Error","message":"Inventory script not available"}), 500
    try:
        inventory_main(section)
    except Exception:
        return jsonify({"status":"Error","message":"Inventory script failed"}), 500
    return jsonify({"status":"Inventory check initiated"}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password')
    env_password = os.getenv('LIBRARIAN_PASSWORD')
    if env_password is None:
        return jsonify({"status":"Error","message":"Server configuration error"}), 500
    if password == env_password:
        return jsonify({"status":"Librarian access granted"}), 200
    return jsonify({"status":"Access denied"}), 401

@app.route('/update_book', methods=['POST'])
def update_book():
    data = parse_yaml_body()
    if not data or 'isbn' not in data:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    response = {
        "status":"Book updated",
        "isbn":data.get('isbn'),
        "new_title":data.get('new_title'),
        "new_author":data.get('new_author'),
        "new_year":data.get('new_year')
    }
    return jsonify(response), 200

@app.route('/delete_book', methods=['POST'])
def delete_book():
    data = parse_yaml_body()
    if not data or 'isbn' not in data:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    return jsonify({"status":"Book deleted","isbn":data.get('isbn')}), 200

@app.route('/generate_reports', methods=['GET'])
def generate_reports():
    report_type = request.args.get('type')
    if not is_valid_identifier(report_type):
        return jsonify({"status":"Error","message":"Invalid report type"}), 400
    if report_main is None:
        return jsonify({"status":"Error","message":"Report generator not available"}), 500
    try:
        report_main(report_type)
    except Exception:
        return jsonify({"status":"Error","message":"Report generation failed"}), 500
    return jsonify({"status":"Report generation started"}), 200

@app.route('/admin_panel', methods=['POST'])
def admin_panel():
    action = request.form.get('action')
    if action == 'backup':
        if backup_main is None:
            return jsonify({"status":"Error","message":"Backup script not available"}), 500
        try:
            backup_main()
        except Exception:
            return jsonify({"status":"Error","message":"Backup failed"}), 500
        return jsonify({"status":"Backup initiated"}), 200
    if action == 'restore':
        if restore_main is None:
            return jsonify({"status":"Error","message":"Restore script not available"}), 500
        try:
            restore_main()
        except Exception:
            return jsonify({"status":"Error","message":"Restore failed"}), 500
        return jsonify({"status":"Restore initiated"}), 200
    return jsonify({"status":"Invalid action"}), 400

@app.route('/view_books', methods=['GET'])
def view_books():
    category = request.args.get('category')
    if not is_valid_identifier(category):
        return jsonify({"status":"Error","message":"Invalid category"}), 400
    if view_books_main is None:
        return jsonify({"status":"Error","message":"View books script not available"}), 500
    try:
        view_books_main(category)
    except Exception:
        return jsonify({"status":"Error","message":"Book view script failed"}), 500
    return jsonify({"status":"Books retrieval initiated","category":category}), 200

@app.route('/add_member', methods=['POST'])
def add_member():
    data = parse_yaml_body()
    if not data or not all(k in data for k in ('name', 'id')):
        return jsonify({"status":"Error","message":"Invalid member information"}), 400
    response = {
        "status":"Member added",
        "name":data.get('name'),
        "id":data.get('id'),
        "membership_date":data.get('membership_date')
    }
    return jsonify(response), 200

@app.route('/update_member', methods=['POST'])
def update_member():
    data = parse_yaml_body()
    if not data or 'id' not in data:
        return jsonify({"status":"Error","message":"Invalid member information"}), 400
    response = {
        "status":"Member updated",
        "id":data.get('id'),
        "new_name":data.get('new_name'),
        "new_date":data.get('new_date')
    }
    return jsonify(response), 200

if __name__ == '__main__':
    app.run(debug=False)