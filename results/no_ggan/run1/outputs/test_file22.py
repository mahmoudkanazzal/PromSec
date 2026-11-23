import os
import re
import subprocess
import yaml
from flask import Flask, jsonify, request

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', 'change_me')

@app.route('/add_book', methods=['POST'])
def add_book():
    raw_data = request.get_data()
    try:
        decoded = raw_data.decode('utf-8')
    except Exception:
        return jsonify(status='Invalid encoding'), 400
    try:
        data = yaml.safe_load(decoded)
    except yaml.YAMLError:
        return jsonify(status='Invalid YAML'), 400
    if not isinstance(data, dict):
        return jsonify(status='Invalid data format'), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify(status='Missing fields'), 400
    return jsonify(status='Book added', title=title)

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'[A-Za-z0-9_-]*', section):
        return jsonify(error='Invalid section'), 400
    subprocess.run(['python', 'inventory_script.py', section], shell=False, check=False)
    return jsonify(status='Inventory check initiated')

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if password == LIBRARIAN_PASSWORD:
        return jsonify(status='Librarian access granted')
    else:
        return jsonify(status='Access denied'), 401

if __name__ == '__main__':
    app.run(debug=False)