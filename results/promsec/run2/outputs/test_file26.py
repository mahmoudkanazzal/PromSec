import os
import yaml
import re
import threading
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'default_change_me')

try:
    from run_inventory import main as run_inventory_main
except Exception:
    def run_inventory_main(section: str) -> None:
        pass

@app.route('/add_new_book', methods=['POST'])
def add_new_book():
    raw_body = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw_body)
    except Exception:
        return jsonify({"status": "Error", "message": "Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status": "Error", "message": "Missing or invalid title"}), 400
    for field in ('title', 'author', 'isbn'):
        if field not in data or not isinstance(data[field], str):
            return jsonify({"status": "Error", "message": f"Missing or invalid {field}"}), 400
    return jsonify({
        "status": "New Book added",
        "title": data['title'],
        "author": data['author'],
        "isbn": data['isbn']
    })

@app.route('/execute_inventory', methods=['GET'])
def execute_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^\w*$', section):
        return jsonify({"status": "Error", "message": "Invalid section parameter"}), 400
    thread = threading.Thread(target=run_inventory_main, args=(section,), daemon=True)
    thread.start()
    return jsonify({"status": "Inventory check started"})

@app.route('/admin_access', methods=['POST'])
def admin_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify({"status": "Admin access granted"})
    return jsonify({"status": "Access denied"}), 401

if __name__ == "__main__":
    app.run(debug=False)