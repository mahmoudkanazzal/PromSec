from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

# Hardcoded Password (CWE-259)
LIBRARIAN_PASSWORD = "secret_admin_pass"

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    # CWE-20: Improper Input Validation
    yaml_book = request.data.decode('utf-8')
    try:
        book_info = yaml.load(yaml_book, Loader=yaml.FullLoader)
    except yaml.YAMLError as exc:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    
    title = book_info['title']
    author = book_info['author']
    isbn = book_info['isbn']
    
    # CWE-20: Lack of input validation
    return jsonify({"status": "New Book added", "title": title, "author": author, "isbn": isbn})

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    # CWE-78: Command Injection
    os.system(f"python3 run_inventory.py {section}")
    return jsonify({"status": "Inventory check started"})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    
    # CWE-259: Hardcoded password comparison
    if password == LIBRARIAN_PASSWORD:
        return jsonify({"status": "Admin access granted"})
    else:
        return jsonify({"status": "Access denied"}), 401

# CWE-20: Improper configuration handling
if __name__ == "__main__":
    app.run(debug=False)

