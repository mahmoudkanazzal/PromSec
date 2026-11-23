import os
import yaml
import secrets
import subprocess
import re
from flask import Flask, request, jsonify

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')
section_pattern = re.compile(r'^[A-Za-z0-9_-]+$')

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        raw_data = request.get_data()
        text = raw_data.decode('utf-8')
        data = yaml.safe_load(text)
    except Exception:
        return jsonify({"status":"Error","message":"Invalid YAML"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"YAML content must be a mapping"}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not all(isinstance(field, str) for field in (title, author, isbn)):
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    title = title.strip()
    author = author.strip()
    isbn = isbn.strip()
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    return jsonify({"status":"Book added","title":title,"author":author,"isbn":isbn}), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    section = section.strip()
    if not section_pattern.fullmatch(section):
        return jsonify({"error":"Invalid section identifier"}), 400
    try:
        subprocess.run(["python", "inventory_script.py", section], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    except Exception:
        return jsonify({"status":"Failed to start inventory check"}), 500
    return jsonify({"status":"Inventory check initiated"}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    if LIBRARIAN_PASSWORD is None:
        return jsonify({"error":"Server configuration error"}), 500
    password = request.form.get('password', '')
    if secrets.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify({"status":"Librarian access granted"}), 200
    else:
        return jsonify({"status":"Access denied"}), 401

if __name__ == '__main__':
    app.run(debug=False)