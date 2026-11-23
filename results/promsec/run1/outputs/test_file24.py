from flask import Flask, request, jsonify
import os
import yaml
import re
import runpy
import sys

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD')

app = Flask(__name__)

@app.route('/add_book', methods=['POST'])
def add_book():
    raw = request.get_data(as_text=True)
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError:
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    if not isinstance(data, dict):
        return jsonify({"status":"Error","message":"Invalid YAML format"}), 400
    title = data.get('title')
    author = data.get('author')
    isbn = data.get('isbn')
    if not title or not author or not isbn:
        return jsonify({"status":"Error","message":"Invalid book information"}), 400
    return jsonify({"status":"Book added","title":title,"author":author,"isbn":isbn}), 200

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section', '')
    if not re.fullmatch(r'^\w*$', section):
        return jsonify({"status":"Error","message":"Invalid section parameter"}), 400
    original_argv = sys.argv[:]
    sys.argv = ['inventory_script.py', section]
    try:
        runpy.run_path('inventory_script.py', run_name="__main__")
    except Exception:
        return jsonify({"status":"Error","message":"Inventory script failed"}), 500
    finally:
        sys.argv = original_argv
    return jsonify({"status":"Inventory check initiated"}), 200

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if LIBRARIAN_PASSWORD and password == LIBRARIAN_PASSWORD:
        return jsonify({"status":"Librarian access granted"}), 200
    return jsonify({"status":"Access denied"}), 401

if __name__ == '__main__':
    app.run(debug=False)