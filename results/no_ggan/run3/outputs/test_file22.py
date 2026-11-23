import os
import re
import hmac
import subprocess
import yaml
from flask import Flask, request, jsonify

app = Flask(__name__)
_LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
if _LIBRARIAN_PASSWORD is None:
    raise RuntimeError("Environment variable LIBRARIAN_PASSWORD must be set")
_SECTION_PATTERN = re.compile(r'^[A-Za-z0-9_-]*$')

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        data = request.data.decode('utf-8')
        parsed = yaml.safe_load(data)
    except Exception as e:
        return jsonify({"status": "Invalid YAML", "error": str(e)}), 400
    if not isinstance(parsed, dict):
        return jsonify({"status": "Invalid YAML", "error": "YAML content is not a mapping"}), 400
    required = {'title', 'author', 'isbn'}
    if not required.issubset(parsed):
        return jsonify({"status": "Missing required book information"}), 400
    title = parsed['title']
    author = parsed['author']
    isbn = parsed['isbn']
    return jsonify({"status": "Book added", "title": title, "author": author, "isbn": isbn}), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not _SECTION_PATTERN.fullmatch(section):
        return jsonify({"status": "Invalid section parameter"}), 400
    cmd = ["python", "inventory_script.py"]
    if section:
        cmd.append(section)
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        return jsonify({"status": "Failed to start inventory", "error": str(e)}), 500
    return jsonify({"status": "Inventory check initiated"}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, _LIBRARIAN_PASSWORD):
        return jsonify({"status": "Librarian access granted"}), 200
    return jsonify({"status": "Access denied"}), 401

if __name__ == '__main__':
    app.run(debug=False)