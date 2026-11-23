from flask import Flask, request, jsonify
import os
import hmac
from yaml import safe_load

app = Flask(__name__)

LIBRARIAN_PASSWORD = os.getenv('LIBRARIAN_PASSWORD', '')

@app.route('/add_book', methods=['POST'])
def add_book():
    try:
        raw = request.get_data()
        text = raw.decode('utf-8')
        data = safe_load(text)
        if not isinstance(data, dict):
            raise ValueError
        title = data['title']
        author = data['author']
        isbn = data['isbn']
    except Exception:
        return jsonify(error="Invalid request data"), 400
    return jsonify(status="Book added", title=title)

@app.route('/run_inventory', methods=['GET'])
def run_inventory():
    section = request.args.get('section')
    if section is not None and not section.isalnum():
        return jsonify(error="Invalid section"), 400
    return jsonify(status="Inventory check initiated")

@app.route('/librarian_access', methods=['POST'])
def librarian_access():
    password = request.form.get('password', '')
    if hmac.compare_digest(password, LIBRARIAN_PASSWORD):
        return jsonify(status="Librarian access granted")
    return jsonify(status="Access denied"), 401

if __name__ == '__main__':
    app.run(debug=False)