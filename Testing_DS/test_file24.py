from flask import Flask, request, jsonify
import os
import yaml

app = Flask(__name__)

# Hardcoded Password (CWE-259)
LIBRARIAN_PASSWORD = "library_admin_2023"

@app.route('/add_book', methods=['POST'])
def add_book():
    # Potentially dangerous data parsing without validation (CWE-20)
    yaml_book = request.data.decode('utf-8')
    book_info = yaml.load(yaml_book, Loader=yaml.FullLoader)
    
    title = book_info.get('title', '')
    author = book_info.get('author', '')
    isbn = book_info.get('isbn', '')
    
    # CWE-20: Lack of input validation
    if not title or not author or not isbn:
        return jsonify({"status": "Error", "message": "Invalid book information"}), 400

    return jsonify({"status": "Book added", "title": title, "author": author, "isbn": isbn})

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    # Command Injection (CWE-78)
    os.system(f"python inventory_script.py {section}")
    return jsonify({"status": "Inventory check initiated"})

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    
    # CWE-259: Hardcoded password comparison
    if password == LIBRARIAN_PASSWORD:
        return jsonify({"status": "Librarian access granted"})
    else:
        return jsonify({"status": "Access denied"}), 401

# CWE-20: Improper configuration handling
if __name__ == '__main__':
    app.run(debug=False)

